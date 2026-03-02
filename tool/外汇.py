import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time


class ForeignExchangeDataCollector:
    def __init__(self):
        self.base_url = "https://www.safe.gov.cn/AppStructured/hlw/RMBQuery.do"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def get_data(self, start_date="2021-01-01", end_date=None):
        """
        Get foreign exchange rate data from SAFE website

        Parameters:
        start_date: Start date (format: YYYY-MM-DD)
        end_date: End date (format: YYYY-MM-DD), default is today
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # Set parameters
        params = {"startDate": start_date, "endDate": end_date, "queryYN": "true"}

        try:
            print(f"Fetching foreign exchange data from {start_date} to {end_date}...")

            # Send GET request
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            time.sleep(1)
            tables = soup.find_all("table")

            if len(tables) >= 5:
                # Get the 5th table (index 4)
                target_table = tables[4]

                # Get all rows
                rows = target_table.find_all("tr")

                if len(rows) == 0:
                    print("No data found in table")
                    return None

                # Extract headers
                header_row = rows[0]
                headers = [
                    cell.get_text(strip=True)
                    for cell in header_row.find_all(["td", "th"])
                ]

                # Add sequence column
                headers.insert(0, "Sequence")

                # Extract data rows
                data = []
                for i, row in enumerate(rows[1:], start=1):  # Skip header
                    cells = row.find_all(["td", "th"])
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    row_data.insert(0, str(i))  # Add sequence number
                    data.append(row_data)

                # Create DataFrame
                df = pd.DataFrame(data, columns=headers)

                print(f"Successfully fetched {len(df)} records")
                return df

            else:
                print("Target table not found")
                return None

        except requests.RequestException as e:
            print(f"Network request error: {e}")
            return None
        except Exception as e:
            print(f"Error processing data: {e}")
            return None

    def save_data(self, df, filename=None):
        """Save data to Excel file"""
        if df is None or df.empty:
            print("No data to save")
            return False

        if filename is None:
            filename = (
                f"foreign_exchange_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )

        try:
            df.to_excel(filename, index=False)
            print(f"Data saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    def get_recent_30_days_data(self):
        """Get data for the last 30 days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        return self.get_data(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )


if __name__ == "__main__":
    # Create collector instance
    collector = ForeignExchangeDataCollector()

    # Get data for specified date range
    df = collector.get_data("2021-01-01", "2025-08-21")

    # Save data
    if df is not None:
        collector.save_data(df)

        # Display first few rows
        print("\nFirst 5 rows:")
        print(df.head())

        # Display data statistics
        print(f"\nTotal records fetched: {len(df)}")

    # Example of getting recent 30 days data
    # df_recent = collector.get_recent_30_days_data()
    # if df_recent is not None:
    #     collector.save_data(df_recent, "recent_30_days_foreign_exchange.xlsx")
