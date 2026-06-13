CREATE DATABASE IF NOT EXISTS db_crochet;
USE db_crochet;

CREATE TABLE customers (
  customer_id int NOT NULL AUTO_INCREMENT,
  name varchar(100) NOT NULL,
  email varchar(150) NOT NULL,
  phone varchar(20) NOT NULL,
  address text NOT NULL,
  PRIMARY KEY (customer_id),
  UNIQUE KEY email (email)
);

CREATE TABLE products (
  product_id int NOT NULL AUTO_INCREMENT,
  title varchar(150) NOT NULL,
  description text,
  category varchar(100) NOT NULL,
  price decimal(10,2) NOT NULL,
  quantity int NOT NULL,
  available int NOT NULL,
  image_path varchar(255) DEFAULT NULL,
  PRIMARY KEY (product_id)
);

CREATE TABLE orders (
  order_id int NOT NULL AUTO_INCREMENT,
  customer_id int DEFAULT NULL,
  product_id int NOT NULL,
  order_date timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  quantity_ordered int NOT NULL,
  total_price decimal(10,2) NOT NULL,
  status varchar(20) NOT NULL DEFAULT 'Pending',
  customer_name varchar(100) DEFAULT NULL,
  customer_email varchar(150) DEFAULT NULL,
  customer_phone varchar(20) DEFAULT NULL,
  customer_address text,
  payment_method varchar(20) NOT NULL DEFAULT 'Online',
  PRIMARY KEY (order_id),
  KEY product_id (product_id),
  KEY customer_id (customer_id),
  CONSTRAINT orders_ibfk_1 FOREIGN KEY (product_id) REFERENCES products (product_id),
  CONSTRAINT orders_ibfk_2 FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

CREATE TABLE investments (
  investment_id int NOT NULL AUTO_INCREMENT,
  amount decimal(10,2) NOT NULL,
  description text NOT NULL,
  date timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (investment_id)
);
