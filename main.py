import os
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv #Reads and loads .env content for os
from google import genai

#Read .env into memory
load_dotenv()

#Initialisng variables
DATA_PATH = "data/master_stock_data.csv"
TICKERS_TO_ANALYSE = ["META", "AMZN", "AAPL", "NFLX", "GOOGL"] #Using FAANG tickers (although FB is now Meta)
ROLLING_WINDOW_DAYS = 30

#Loading and cleaning stock database
def load_data(path: str) -> pd.DataFrame: 
    df = pd.read_csv(path)
    
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns] #Removes edge whitespace, replaces spaces with "_", removes capitals for each column name
    
    df["date"] = pd.to_datetime(df["date"]) #Converts plain text to understandble datetime type for pandas
    df = df.sort_values(["ticker", "date"]) #Sorts table by ticker, then by date within each ticker
    
    return df

#Filtering tickers
def filter_tickers(df: pd.DataFrame, tickers: list[str]):
    available = set(df["ticker"].unique()) #Creates an unordered set of unique tickers
    missing = [t for t in tickers if t not in available] #Self explanatory
    if missing:
        print(f"Note: these tickers weren't found in the dataset and will be skipped: {missing}")
    return df[df["ticker"].isin(tickers)].copy() #Dataframe with list of available tickers for analysis

#Plotting 
def plot_price_and_volatility(df: pd.DataFrame):
    fig, axes = plt.subplot(2, 1, figsize=(10, 8), sharex=True) #Figure with 2 rows 1 column of subplots, both charts share x axis
    
    for ticker, group in df.groupby("ticker"): 
        axes[0].plot(group["date"], group["close"], labels=ticker)
        axes[1].plot(group["date"], group["rolling_volatility"], label=ticker)
        
    axes[0].set_title("Closing price over time")
    axes[0].legend()
    axes[1].set_title(f"{ROLLING_WINDOW_DAYS}-day rolling volatility of daily returns")
    axes[1].legend()

    plt.tight_layout()
    
#Creating a summary of data to send to the LLM - can't read dataframes
def build_summary(df: pd.DataFrame) -> str:
    lines = [] #List of summaries per ticker
    for ticker, group in df.groupby("ticker"): 
        avg_return = group["daily_return"].mean()
        avg_vol = group["rolling_volatity"].mean()
        lines.append(
            f"{ticker}: average daily return = {avg_return}, "
            f"average {ROLLING_WINDOW_DAYS}-day rolling volatility = {avg_vol}:.4%"
        ) #Adds strings to 'lines' where decimals are diplayed as percentages to 4dp
    return "/n".join(lines) #Glues items in 'lines' together

#Calling Gemini
def ask_gemini_about_data(question: str, summary: str) -> str:
    genai.Client(api_key=os.environ["GEMINI_API_KEY"]) #Looks up value from .env
    prompt = f"""You are a data analyst assistant. Here is a summary of a stock dataset:
        
    {summary}
        
    Answer this question about the data as clearly and consisely as possible,
    referencing the actual numbers when relevant:
            
    {question}
    """
    
    response = client.models.generate_content( #API call
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text #Extracts the generated answer as a string

#The main execution block
if __name__ == "__main__": #Standard python convention - only runs if file is run directly not if functions were imported
    df = load_data(DATA_PATH)
    df = filter_tickers(df, TICKERS_TO_ANALYSE)
    
    print(df.head())
    
    plot_price_and_volatility(df)
    
    summary = build_summary(df)
    print("\nSummary stats:\n", summary)
    
    question = "Which stock had the highest volatility, and what might explain that?"
    answer = ask_gemini_about_data(question, summary)

    print(f"/nQuestion: {question}")
    print(f"Answer: {answer}")