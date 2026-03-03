CREATE TABLE nifty50_5m (
	stock_id        INT             NOT NULL PRIMARY KEY auto_increment,
    date            BIGINT          NOT NULL,  
    open            DECIMAL(12,4)   NOT NULL,               
    high            DECIMAL(12,4)   NOT NULL,
    low             DECIMAL(12,4)   NOT NULL,
    close           DECIMAL(12,4)   NOT NULL,
    volume          DECIMAL(18,8)   NOT NULL DEFAULT 0      
);

CREATE TABLE nifty100_5m (
	stock_id        INT             NOT NULL PRIMARY KEY auto_increment,
    date            BIGINT          NOT NULL,  
    open            DECIMAL(12,4)   NOT NULL,               
    high            DECIMAL(12,4)   NOT NULL,
    low             DECIMAL(12,4)   NOT NULL,
    close           DECIMAL(12,4)   NOT NULL,
    volume          DECIMAL(18,8)   NOT NULL DEFAULT 0      
);

CREATE TABLE nifty500_5m (
	stock_id        INT             NOT NULL PRIMARY KEY auto_increment,
    date            BIGINT          NOT NULL,  
    open            DECIMAL(12,4)   NOT NULL,               
    high            DECIMAL(12,4)   NOT NULL,
    low             DECIMAL(12,4)   NOT NULL,
    close           DECIMAL(12,4)   NOT NULL,
    volume          DECIMAL(18,8)   NOT NULL DEFAULT 0      
);

-- USE OF COUNT COMMAND TO SHOW NUMBER OF VALUES RECORDED IN DATA
SELECT COUNT(*) FROM nifty100.nifty50_5m;
SELECT COUNT(*) FROM nifty100.nifty100_5m;
SELECT COUNT(*) FROM nifty100.nifty500_5m;


-- USE OF UNION JOIN TO SHOW ENTRIES ACROSS ALL TABLES IN A SINGLE TABLE

SELECT 
    'NIFTY50' AS index_name,
    stock_id,
    date AS datetime_start,
    open, high, low, close, volume
FROM nifty50_5m

UNION ALL

SELECT 
    'NIFTY100' AS index_name,
    stock_id,
    date AS datetime_start,
    open, high, low, close, volume
FROM nifty100_5m

UNION ALL

SELECT 
    'NIFTY500' AS index_name,
    stock_id,
    date AS datetime_start,
    open, high, low, close, volume
FROM nifty500_5m;   

-- USE OF INNER JOIN TO SHOW ONLY THE MOMENTS PRESENT IN BOTH NIFTY 50 AND NIFTY 100
-- IT IS ALSO BEING USED TO CHECK WHICH OF THE BOTH INDICES WERE HIGHER AT THE CLOSE PRICE AS A COMPARISON (positive = Nifty 50 was higher, negative = Nifty 100 was higher)

SELECT 
    a.date,
    a.close AS nifty50_close,
    b.close AS nifty100_close,
    (a.close - b.close) AS difference
FROM nifty50_5m a
INNER JOIN nifty100_5m b 
    ON a.date = b.date
ORDER BY a.date;

-- TO FIND THE STANDARD DEVIATION OF CLOSE PRICE ACROSS ALL THREE INDICES 

SELECT 
    index_name,
    DATE(date) AS trading_date,
    STDDEV(close) AS daily_volatility
FROM (
    SELECT 'NIFTY50' AS index_name, date, close FROM nifty50_5m
    UNION ALL
    SELECT 'NIFTY100' AS index_name, date, close FROM nifty100_5m
    UNION ALL
    SELECT 'NIFTY500' AS index_name, date, close FROM nifty500_5m
) t         -- TABLE NAME
WHERE date >= '2026-01-21' AND date < '2026-01-22'
GROUP BY index_name, trading_date;

-- AVERAGE PRICE ON TRADING DAYS FOR ALL THREE INDICES

CREATE TABLE nifty50_daily AS
SELECT 
    DATE(date) AS trading_day,
    AVG(close) AS avg_close,
    AVG(open)  AS avg_open,
    MAX(high)  AS day_high,
    MIN(low)   AS day_low,
    COUNT(*)   AS bars_count
FROM nifty50_5m
GROUP BY DATE(date);

CREATE TABLE nifty100_daily AS
SELECT 
    DATE(date) AS trading_day,
    AVG(close) AS avg_close,
    AVG(open)  AS avg_open,
    MAX(high)  AS day_high,
    MIN(low)   AS day_low,
    COUNT(*)   AS bars_count
FROM nifty100_5m
GROUP BY DATE(date);

CREATE TABLE nifty500_daily AS
SELECT 
    DATE(date) AS trading_day,
    AVG(close) AS avg_close,
    AVG(open)  AS avg_open,
    MAX(high)  AS day_high,
    MIN(low)   AS day_low,
    COUNT(*)   AS bars_count
FROM nifty500_5m
GROUP BY DATE(date);

SELECT * FROM nifty100.nifty50_daily;
SELECT * FROM nifty100.nifty100_daily;
SELECT * FROM nifty100.nifty500_daily;

-- OVERALL MIN/MAX FOR CLOSE PRICES FOR ALL RECORDED DATA

SELECT 
    'NIFTY50' AS index_name,
    (SELECT MIN(close) FROM nifty50_5m)   AS min_close,
    (SELECT date   FROM nifty50_5m WHERE close = (SELECT MIN(close) FROM nifty50_5m) LIMIT 1) AS min_date,
    (SELECT MAX(close) FROM nifty50_5m)   AS max_close,
    (SELECT date   FROM nifty50_5m WHERE close = (SELECT MAX(close) FROM nifty50_5m) LIMIT 1) AS max_date

UNION

SELECT 
    'NIFTY100' AS index_name,
    (SELECT MIN(close) FROM nifty100_5m)   AS min_close,
    (SELECT date   FROM nifty100_5m WHERE close = (SELECT MIN(close) FROM nifty100_5m) LIMIT 1) AS min_date,
    (SELECT MAX(close) FROM nifty100_5m)   AS max_close,
    (SELECT date   FROM nifty100_5m WHERE close = (SELECT MAX(close) FROM nifty100_5m) LIMIT 1) AS max_date
    
UNION

SELECT 
    'NIFTY500' AS index_name,
    (SELECT MIN(close) FROM nifty500_5m)   AS min_close,
    (SELECT date   FROM nifty500_5m WHERE close = (SELECT MIN(close) FROM nifty500_5m) LIMIT 1) AS min_date,
    (SELECT MAX(close) FROM nifty500_5m)   AS max_close,
    (SELECT date   FROM nifty500_5m WHERE close = (SELECT MAX(close) FROM nifty500_5m) LIMIT 1) AS max_date;