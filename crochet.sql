create database db_crochet;
use db_crochet;
CREATE TABLE IF NOT EXISTS orders (
	order_id INT AUTO_INCREMENT,
	user_id	INT NOT NULL,
	product_id	INT NOT NULL,
	order_date	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	quantity_ordered INT NOT NULL,
	total_price	decimal(10,2) NOT NULL,
	PRIMARY KEY(order_id),
	FOREIGN KEY(product_id) REFERENCES products(product_id),
	FOREIGN KEY(user_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS products (
	product_id	INT AUTO_INCREMENT,
	title	VARCHAR(150) NOT NULL,
	description	TEXT,
	category	VARCHAR(100) NOT NULL,
	price	decimal(10,2) NOT NULL,
	quantity	INT NOT NULL,
	available	INT NOT NULL,
	PRIMARY KEY(product_id)
);
CREATE TABLE IF NOT EXISTS users (
	user_id	INT AUTO_INCREMENT,
	name VARCHAR(100) NOT NULL,
	email	VARCHAR(150) NOT NULL UNIQUE,
	phone	VARCHAR(20) NOT NULL,
	address	TEXT NOT NULL,
	PRIMARY KEY(user_id)
);
INSERT INTO orders VALUES (1,2,7,'2026-05-31 12:19:25',1,5.97);
INSERT INTO orders VALUES (2,3,1,'2026-05-31 12:21:34',2,36.0);
INSERT INTO products VALUES (1,'Strawberry Plushie','A soft, chunky crocheted strawberry with a smiling face. Perfect for gifting!','Plushies',18.0,12,10);
INSERT INTO products VALUES (2,'Cloud Bear Plushie','Dreamy pastel bear stuffed with love. Hand-finished with embroidered eyes.','Plushies',22.5,8,8);
INSERT INTO products VALUES (3,'Floral Cardigan','Vintage-inspired open-front cardigan in blush pink with floral yoke detail.','Cardigans',85.0,5,5);
INSERT INTO products VALUES (4,'Cottagecore Vest','Earthy tones, cropped fit. Great for layering over blouses.','Cardigans',65.0,4,4);
INSERT INTO products VALUES (5,'Mug Cozy – Autumn','Keep your tea warm in this fall-themed mug sleeve with leaf motifs.','Cozies',12.0,20,20);
INSERT INTO products VALUES (6,'Book Sleeve','A padded crochet sleeve to protect your favorite novel.','Cozies',15.0,10,10);
INSERT INTO products VALUES (7,'Mrs. Honeybun','a cute crocheted teddy bear to keep your trinkets, glasses and all things dear to you save whilst adding a little whimsy to your home.','Home Décor',5.97,3,2);
INSERT INTO users VALUES (1,'Rose Whitmore','rose@example.com','555-0101','12 Bluebell Lane, Cotswold, UK');
INSERT INTO users VALUES (2,'Lily Fairfax','lily@example.com','555-0202','3 Primrose Ave, Bath, UK');
INSERT INTO users VALUES (3,'Hafsa Wajid','hafsawajidq22@gmail.com','12346789','shiganshina district');

