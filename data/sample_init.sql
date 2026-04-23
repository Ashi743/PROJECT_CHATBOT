-- Sample initialization data for SQL analysis tool
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY,
    product TEXT,
    quantity INTEGER,
    price REAL,
    date TEXT
);

INSERT INTO sales (product, quantity, price, date) VALUES
('Wheat', 100, 543.20, '2024-01-15'),
('Corn', 150, 298.50, '2024-01-15'),
('Soy', 80, 720.30, '2024-01-15'),
('Wheat', 120, 545.10, '2024-01-16'),
('Corn', 140, 295.80, '2024-01-16'),
('Sugar', 200, 198.75, '2024-01-16');
