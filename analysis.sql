-- Check to see if the data has loaded
SELECT * FROM STOCK_ANALYSIS.PUBLIC.STOCK_DATA
ORDER BY TICKER, DATE
LIMIT 10;
 
-- Daily returns using window function
SELECT TICKER, DATE, CLOSE,
    (CLOSE - LAG(CLOSE) OVER (PARTITION BY TICKER ORDER BY DATE)) / LAG(CLOSE) OVER (PARTITION BY TICKER ORDER BY DATE)
    -- LAG() grabs the previous row's value, needed for returns
    AS daily_return
FROM STOCK_ANALYSIS.PUBLIC.STOCK_DATA
WHERE TICKER IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META')
ORDER BY TICKER, DATE
LIMIT 20;
 
-- Using a Common Table Expression to create a Rolling Volatility column
WITH daily_returns AS (
    SELECT TICKER, DATE, CLOSE,
        (CLOSE - LAG(CLOSE) OVER (PARTITION BY TICKER ORDER BY DATE)) / LAG(CLOSE) OVER (PARTITION BY TICKER ORDER BY DATE) AS daily_return
    FROM STOCK_ANALYSIS.PUBLIC.STOCK_DATA
    WHERE TICKER IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META')
)
 
SELECT TICKER, DATE, daily_return,
    STDDEV(daily_return) OVER (
        PARTITION BY TICKER ORDER BY DATE
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        -- this includes this row and the 29 before it in the calculation
    ) AS rolling_volatility
FROM daily_returns
ORDER BY TICKER, DATE
LIMIT 50;
 
-- Creating a summary by collapsing all daily rows into one summary row per ticker
WITH daily_returns AS (
    SELECT TICKER, DATE, CLOSE,
        (CLOSE - LAG(CLOSE) OVER (PARTITION BY TICKER ORDER BY DATE)) / LAG(CLOSE) OVER (PARTITION BY TICKER ORDER BY DATE) AS daily_return
    FROM STOCK_ANALYSIS.PUBLIC.STOCK_DATA
    WHERE TICKER IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META')
),
 
with_volatility AS (
    SELECT TICKER, DATE, daily_return,
        STDDEV(daily_return) OVER (PARTITION BY TICKER ORDER BY DATE ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS rolling_volatility
    FROM daily_returns
)
 
SELECT TICKER,
    AVG(daily_return) AS average_daily_return,
    AVG(rolling_volatility) AS average_rolling_volatility
FROM with_volatility
GROUP BY TICKER
ORDER BY average_rolling_volatility DESC;