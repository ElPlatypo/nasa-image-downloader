# NasaImageDownloader

![img](img/iss.jpg)
(Image is ai generated)

This Python script allows you to scrape and organize images from the NASA International Space Station (ISS) database. It fetches image metadata from the NASA database, downloads image files, and provides various operations to manage and group the images based on specified criteria.

## Requirements

- Python 3.x
- Pandas library
- Requests library

Install the required libraries using the following command:
```pip install pandas requests```

## Usage

1. Download the script and save it as `nasa_iss_scraper.py`.

2. Open a terminal or command prompt and navigate to the directory containing the script.

3. Run the script using the following command:
```python nasa_iss_scraper.py```

Follow the on-screen instructions to perform various operations:

- `d`: Download raw database and build true database.
- `b`: Build true database.
- `gt`: Group images based on delta-time and minimum consecutive frames.
- `ds`: Download image sequences from a search folder.
- `q`: Quit the program.

## Note

Please be aware that this script scrapes data from the NASA website. Make sure to review and adhere to NASA's terms of use and guidelines for accessing their data.

## Disclaimer

This script was created for educational purposes and convenience in accessing publicly available data from the NASA ISS database. Use it responsibly and ensure compliance with NASA's data usage policies.