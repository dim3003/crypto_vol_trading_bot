import unittest
import numpy as np
import get_crypto_names as gcn

#check if all tokens from pg database have an address and decimals with get_tokens from bot.py

class Test(unittest.TestCase):
    def test_1inch_colnames(self):
        """
        Test that get crypto names 1inch fetcher has all columns needed
        """
        col_names = np.array(['address', 'chainId', 'name', 'symbol', 'decimals', 'logoURI'])
        r = gcn.get_tokens_1inch().columns.values
        self.assertEqual(len(col_names), len(r))
        
        for i in range(len(col_names)):
            if r[i]!=col_names[i]:
                print(f"{r[i]} != the test column {col_names[i]}")
                self.assertEqual(0,1,f"The column {r[i]} is not the same as the test column {col_names[i]}")

        if len(r)==0:
            x = 1
            self.assertEqual(0,1,"There is nothing in the 1inch dataframe :/") 


if __name__ == '__main__':
    unittest.main()