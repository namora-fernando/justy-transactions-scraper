# 🕷️ Justy Transactions Scraper  

Automated web scraping tool built with **Python + Selenium** to extract transaction data from **Justy Café’s POS system**.  
This scraper was developed for internal analytics purposes and powers the dataset used in the [Justy Sales Dashboard](https://github.com/namora-fernando/justy-sales-dashboard).  

⚠️ **Disclaimer**:  
- This project is not affiliated with, endorsed by, or officially connected to **ESB POS** in any way.  
- The scraper was built as a workaround for missing export features and is intended only for internal analytics.  

---

## ✨ Features  
- 🔄 Automated scraping of POS transaction history  
- 📂 Export transactions into CSV format for downstream analytics (e.g., Power BI)  
- ⚡ Scales to handle thousands of transactions without manual copy-paste  

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

## 🚀 Usage  

1. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the scraper**
   ```bash
   python justy-scraper-transactions.py
   ```
3. **Output**
   - Scraped transactions will be saved in the `output/` folder as CSV files, same location as the py file
   - The sample transaction located in the `sample_data/` folder in this repository

---

## 🔒 Data Privacy

This project contains **no sensitive business data**. The permission already given by the owner of the cafe.
