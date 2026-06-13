import pymysql

MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'tatakae139'
MYSQL_DB = 'db_crochet'

def update_schema():
    connection = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        autocommit=True
    )
    
    with connection.cursor() as cursor:
        try:
            cursor.execute("ALTER TABLE orders DROP FOREIGN KEY orders_ibfk_2;")
            print("Dropped foreign key")
        except Exception as e:
            print("Error dropping FK:", e)
            
        try:
            cursor.execute("RENAME TABLE users TO customers;")
            print("Renamed table")
        except Exception as e:
            print("Error renaming table:", e)
            
        try:
            cursor.execute("ALTER TABLE customers CHANGE user_id customer_id int NOT NULL AUTO_INCREMENT;")
            print("Changed pk name")
        except Exception as e:
            print("Error changing pk:", e)
            
        try:
            cursor.execute("ALTER TABLE orders CHANGE user_id customer_id int DEFAULT NULL;")
            print("Changed fk name")
        except Exception as e:
            print("Error changing fk:", e)
            
        try:
            cursor.execute("ALTER TABLE orders DROP INDEX user_id;")
        except Exception as e:
            print("Error dropping index:", e)
            
        try:
            cursor.execute("ALTER TABLE orders ADD INDEX customer_id (customer_id);")
            print("Added index")
        except Exception as e:
            print("Error adding index:", e)
            
        try:
            cursor.execute("ALTER TABLE orders ADD CONSTRAINT orders_ibfk_2 FOREIGN KEY (customer_id) REFERENCES customers (customer_id);")
            print("Added fk constraint")
        except Exception as e:
            print("Error adding fk:", e)

    connection.close()

if __name__ == '__main__':
    update_schema()
