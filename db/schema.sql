-- Create `puppy` table
CREATE TABLE IF NOT EXISTS puppy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    gender TEXT NOT NULL,
    age INTEGER NOT NULL,
    price REAL NOT NULL,
    dob TEXT NOT NULL,
    color TEXT,
    variety TEXT,
    images TEXT,
    about TEXT,
    mom_weight TEXT,
    mom_color TEXT,
    dad_color TEXT,
    dad_weight TEXT,
    mom_image TEXT,
    dad_image TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    puppy_id INTEGER NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(100) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    customer_address TEXT NOT NULL,
    status INTEGER DEFAULT 1, -- 1: Order Received, 2: Scheduled, 3: Out for Delivery, 4: Delivered
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_puppy
      FOREIGN KEY (puppy_id)
      REFERENCES puppy(id)
      ON DELETE CASCADE
);
-- Create `settings` table
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logo TEXT,
    phonenumber TEXT,
    site_name TEXT,
    email TEXT,
    password TEXT
);

-- Create `review` table
CREATE TABLE IF NOT EXISTS review (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    picture TEXT,
    review_text TEXT,
    date TEXT
);

-- Create `traffic` table
CREATE TABLE IF NOT EXISTS traffic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    visits INTEGER NOT NULL
);
