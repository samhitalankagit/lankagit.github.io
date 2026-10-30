import sys, unittest
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from bidlens_engine import load_extracted_dataset, normalize_price, optimize_allocation, simulate_split_allocation, SUPPLIERS

class BidLensEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items,cls.quotes,cls.sources=load_extracted_dataset()
        cls.gold=pd.read_csv(ROOT/"data"/"gold_standard_quotes.csv")

    def test_expected_scope(self):
        self.assertEqual(len(self.items),30)
        self.assertEqual(self.items.family.nunique(),3)
        self.assertEqual(len(self.quotes),150)
        self.assertEqual(self.quotes.supplier_id.nunique(),5)

    def test_all_bundled_sources_parse_expected_quoted_values(self):
        for sid in self.quotes.supplier_id.unique():
            actual=self.quotes[(self.quotes.supplier_id==sid)&self.quotes.quoted_price.notna()].set_index("item_id")
            gold=self.gold[(self.gold.supplier_id==sid)&self.gold.quoted_price.notna()].set_index("item_id")
            self.assertEqual(set(actual.index),set(gold.index),sid)
            for item_id in actual.index:
                self.assertAlmostEqual(float(actual.loc[item_id,"quoted_price"]),float(gold.loc[item_id,"quoted_price"]),places=2,msg=f"{sid} {item_id}")
                self.assertEqual(str(actual.loc[item_id,"currency"]),str(gold.loc[item_id,"currency"]))
                self.assertEqual(str(actual.loc[item_id,"price_basis"]).lower(),str(gold.loc[item_id,"price_basis"]).lower())

    def test_missing_and_ambiguous_values_are_not_zero(self):
        self.assertTrue(self.quotes[(self.quotes.supplier_id=="SUP-B")&(self.quotes.item_id=="BX-08")].quoted_price.isna().all())
        c=self.quotes[(self.quotes.supplier_id=="SUP-C")&(self.quotes.item_id=="BX-13")].iloc[0]
        self.assertTrue(pd.isna(c.quoted_price))
        self.assertIn("ambiguous",c.issue.lower())
        self.assertEqual(c.original_price_text,"8.?")

    def test_normalization_is_explicit(self):
        self.assertEqual(normalize_price(100,"INR","per 100 items",83),1.0)
        self.assertEqual(normalize_price(10,"USD","per item",83),830.0)
        self.assertIsNone(normalize_price(10,"EUR","per item",83))
        self.assertIsNone(normalize_price(None,"INR","per item",83))

    def test_scenario_obeys_delivery_and_supplier_count(self):
        result=optimize_allocation(self.quotes,self.items,83,7,2,True,"cost")
        self.assertTrue(result["feasible"],result.get("reason"))
        self.assertEqual(len(result["assignments"]),30)
        self.assertLessEqual(result["max_delivery_days"],7)
        self.assertLessEqual(result["supplier_count"],2)
        self.assertGreater(result["total_known_cost"],0)
        self.assertNotIn("Metro Pack Hyderabad (Sample)",result["suppliers"])
        self.assertIn("Unconfirmed discounts are not applied.",result["limitations"])


    def test_supplier_tax_treatment_is_extracted_and_not_assumed(self):
        tax=self.quotes.groupby("supplier_id").tax_status.first().to_dict()
        self.assertEqual(tax["SUP-A"],"GST included in quoted prices")
        self.assertEqual(tax["SUP-B"],"Not stated in source document")
        self.assertEqual(tax["SUP-D"],"Not stated in source document")

    def test_split_simulation_allocates_requested_quantities_and_keeps_evidence(self):
        result=simulate_split_allocation(self.quotes,self.items,"SUP-A","SUP-B",70,83,7,True)
        self.assertTrue(result["feasible"],result.get("reason"))
        self.assertEqual(result["supplier_count"],2)
        by_item={}
        for row in result["assignments"]:
            by_item.setdefault(row["Item ID"],0)
            by_item[row["Item ID"]]+=row["Allocated quantity"]
            self.assertTrue(row["Evidence"])
            self.assertTrue(row["Source excerpt"])
        for row in self.items.itertuples():
            self.assertEqual(by_item[row.item_id],int(row.quantity))
        self.assertIn("not an optimized allocation", " ".join(result["limitations"]).lower())

    def test_source_files_exist(self):
        for supplier in SUPPLIERS:
            self.assertTrue((ROOT/"data"/"source_documents"/supplier["source_file"]).exists())

if __name__=="__main__": unittest.main()
