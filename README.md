# 🕷️ Justy Transactions Scraper  

An automated web scraping program built with **Python and Selenium** to extract detailed transaction-level data from  **Justy Café’s ESB POS system** that does not provide bulk export functionality.

This scraper was developed to overcome limitations of the ESB POS system, where transaction details must be accessed manually on a per-transaction basis. The extracted data is used for internal analytics and serves as the primary data source for the [Justy Sales Dashboard](https://github.com/namora-fernando/justy-sales-dashboard).

⚠️ **Disclaimer**:  
- This project is not affiliated with, endorsed by, or officially connected to **ESB POS** in any way.  
- The scraper was built as a workaround for missing export features from ESB POS and is intended only for internal analytics.
- The data that represented on the sample data, is only a sample of all data. However, the tools can be used for all real data without boundary of the date.

---

## Features  :
- Automated scraping of POS transaction history  
- Export transactions into CSV format for downstream analytics (e.g., Power BI)  
- Scales to handle thousands of transactions without manual copy-paste  

---

## 🛠️ Tech Stack  
- **Python 3.9+**  
- **Selenium** (browser automation)  
- **webdriver-manager** (auto ChromeDriver updates)  
- **pandas** (data cleaning & export)  

---

## 📂 Project Structure  
```bash
justy-transactions-scraper/
│── sample_data/                       # Contains sample transactions as a sample scraped CSV exports
│── justy-scraper-transactions.py      # Main Python script (Selenium + parsing logic)  
│── requirements.txt                   # Python dependencies  
│── README.md                          # Documentation  
```

---

## Usage  

1. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the scraper**
   ```bash
   python justy-scraper-transactions.py
   ```
   *Note:* Please wait for some moment on the first process of the program for installation of packages.
   
3. **Input on programs**
   - Input e-mail and password for account of **ESB POS** to gain access into each account transactions access.
   - When the program ask input the date, only hit `Enter` **after** manually clicked on the popped website, to gain transactional data from starting date until ending date.

   *Note:* After date chosen, no input needed more for this program. Kindly wait until the program finished and website to be closed, the outputs will be saved afterward.

4. **Output**
   - Scraped transactions will be saved in the `output/` folder as CSV files, same location as the py file
   - The sample transaction located in the `sample_data/` folder in this repository

---

## ⚠️ Data Privacy

This project contains **no sensitive business data**. The permission already given by the owner of the café.
