# CartFlow API

CartFlow API is an asynchronous REST API for managing a product catalog, hierarchical categories, shopping carts, and orders.

The project demonstrates JWT authentication, role-based access control, PostgreSQL full-text search, image uploads, filtering, pagination, database transactions, and row-level locking.

## Features

- Asynchronous FastAPI application
- PostgreSQL database
- SQLAlchemy 2.0 with `AsyncSession`
- Alembic database migrations
- User registration and authentication
- Access and refresh JWT tokens
- Password hashing with Argon2
- Role-based permissions
- Hierarchical product categories
- Product image uploading
- Image type and size validation
- Product filtering and pagination
- PostgreSQL full-text search
- One shopping cart per user
- Transactional order creation
- Stock validation and reduction
- Order status transitions
- Stock restoration after cancellation
- Row-level locking with `FOR UPDATE`
- Soft deletion of products and categories

## Technology Stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- asyncpg
- Alembic
- Pydantic 2
- PyJWT
- pwdlib
- Argon2
- Pillow
- python-multipart
- python-dotenv
- Uvicorn

## Project Structure

```text
CartFlow API/
├── app/
│   ├── migrations/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── models/
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── cart.py
│   │   ├── cartitem.py
│   │   ├── order.py
│   │   └── orderitem.py
│   ├── routers/
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── cart.py
│   │   └── order.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── cart.py
│   │   └── order.py
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── db_depends.py
│   ├── dependency.py
│   └── main.py
├── services/
│   └── images.py
├── media/
│   └── products/
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

## Data Model

The application contains seven main entities:

- `User`
- `Category`
- `Product`
- `Cart`
- `CartItem`
- `Order`
- `OrderItem`

### Relationships

```text
User 1 ─── 1 Cart
User 1 ─── M Product
User 1 ─── M Order

Category 1 ─── M Product
Category 1 ─── M Category

Cart 1 ─── M CartItem
Product 1 ─── M CartItem

Order 1 ─── M OrderItem
Product 1 ─── M OrderItem
```

A category can contain child categories through a self-referencing relationship.

A cart stores references to products and their selected quantities. An order stores separate order items so that purchased quantities and prices are preserved after checkout.

## User Roles

The API supports three roles.

### Customer

A customer can:

- manage their own cart;
- create an order from the cart;
- view their own orders;
- view one of their own orders;
- cancel their own pending order;
- delete their account if it has no products or orders.

The `customer` role is assigned automatically during registration.

### Seller

A seller can:

- create products;
- upload product images;
- update their own products;
- replace product images;
- deactivate their own products;
- manage their own cart.

A seller cannot create an order.

### Administrator

An administrator can:

- create, update, and deactivate categories;
- change user roles;
- deactivate any product;
- view all orders;
- filter and paginate orders;
- perform allowed order status transitions;
- delete another eligible user account.

## Authentication

Authentication uses access and refresh JWT tokens.

### Access token

The access token has a short lifetime and is used to access protected endpoints.

```http
Authorization: Bearer ACCESS_TOKEN
```

### Refresh token

The refresh token has a longer lifetime and is used to create a new access token.

The current implementation does not rotate or store refresh tokens in the database.

### Password security

Passwords are never stored directly. During registration, the password is hashed with Argon2 through `pwdlib`.

During authentication, the entered password is compared with the saved hash.

## Categories

Categories support a hierarchical structure using `parent_id`.

A category with:

```json
{
  "name": "Electronics",
  "parent_id": null
}
```

is a root category.

A child category can reference another active category:

```json
{
  "name": "Smartphones",
  "parent_id": 1
}
```

The application prevents:

- assigning a category as its own parent;
- assigning one of its descendants as its parent;
- referencing a missing or inactive parent;
- deactivating a category with active products;
- deactivating a category with active child categories.

Categories use soft deletion:

```text
is_active = false
```

## Products

Only sellers can create products.

Every product belongs to:

- one seller;
- one active category.

Products support:

- partial updates;
- soft deletion;
- optional descriptions;
- optional images;
- stock management;
- filtering;
- pagination;
- PostgreSQL full-text search.

Deactivating a product sets:

```text
is_active = false
```

The product is then excluded from public product queries.

## Product Images

Product creation and updating use `multipart/form-data`.

The following formats are supported:

- JPEG
- PNG
- WebP

The maximum image size is:

```text
2 MiB
```

Uploaded files are:

1. Read asynchronously.
2. Checked against the maximum size.
3. Verified with Pillow.
4. Assigned an extension based on their actual format.
5. Renamed using UUID.
6. Saved inside `media/products/`.
7. Stored in the database as a relative URL.

Example URL:

```text
/media/products/550e8400-e29b-41d4-a716-446655440000.jpg
```

Static files are exposed through:

```python
app.mount(
    "/media",
    StaticFiles(directory=BASE_DIR / "media"),
    name="media",
)
```

Replacing an image removes the previous image after the database transaction succeeds.

Deactivating a product clears its image URL and removes the associated file.

The `media/` directory is excluded from Git.

## Product Search

Products support PostgreSQL full-text search by name and description.

The implementation uses:

- a generated `TSVECTOR` column;
- `websearch_to_tsquery`;
- the `@@` matching operator;
- `ts_rank_cd`;
- a PostgreSQL GIN index.

Product names have priority `A`, while descriptions have priority `B`.

Matching products are sorted first by relevance and then by product ID.

## Product Filtering and Pagination

`GET /products/` supports the following query parameters:

| Parameter | Description |
|---|---|
| `page` | Current page number |
| `page_size` | Number of products per page |
| `seller_id` | Filter by seller |
| `category_id` | Filter by category |
| `search` | Full-text search |
| `in_stock` | Filter by stock availability |
| `min_price` | Minimum price |
| `max_price` | Maximum price |

Example:

```http
GET /products/?page=1&page_size=20&category_id=2&search=wireless+headphones&in_stock=true&min_price=50&max_price=500
```

The response contains:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

The default page size is `20`, and the maximum page size is `100`.

Category filtering currently searches only inside the specified category and does not automatically include its descendants.

## Shopping Cart

Each user receives one shopping cart during registration.

A cart item contains:

- `product_id`;
- selected `quantity`;
- current product information.

When the same product is added again, its quantity in the cart is increased.

Updating a cart item replaces its quantity with the new value.

Users can:

- view their cart;
- add a product;
- update product quantity;
- remove one cart item;
- remove all cart items.

Adding a product to the cart does not reserve its stock. Availability is checked again during checkout.

## Order Creation

Only customers can create orders.

`POST /order/` does not require a request body because the order is created from the current user's cart.

Checkout is performed as one database transaction:

1. The user's cart is locked.
2. Cart items are loaded.
3. The cart is checked for emptiness.
4. Products are sorted by ID.
5. Every product is locked with `FOR UPDATE`.
6. Product availability is checked.
7. Current product prices are used.
8. The order and its items are created.
9. Product quantities are reduced.
10. Cart items are deleted.
11. The transaction is committed.

If any operation fails, the transaction is rolled back.

## Order Prices

`Order.price` stores the total amount of the order.

`OrderItem.price` stores the total price of one order position:

```text
product price × quantity
```

For example:

```text
Product price: 100.00
Quantity: 3
OrderItem.price: 300.00
```

The stored order price is not changed when the current product price changes later.

## Order Statuses

Available statuses:

```text
pending
paid
completed
cancelled
```

Allowed transitions:

```text
pending -> paid
pending -> cancelled
paid -> completed
```

The statuses `completed` and `cancelled` are final.

A customer can only cancel their own pending order.

An administrator can perform all allowed transitions.

When an order is cancelled, its quantities are returned to product stock.

## Order Filtering and Pagination

Administrators can use `GET /order/orderlist/admin`.

Supported parameters:

| Parameter | Description |
|---|---|
| `page` | Current page |
| `page_size` | Items per page |
| `order_id` | Filter by order ID |
| `status` | Filter by status |
| `create_with` | Minimum creation date |
| `create_up` | Maximum creation date |
| `min_price` | Minimum order amount |
| `max_price` | Maximum order amount |

Dates must include timezone information.

Valid examples:

```text
2026-09-01T10:00:00Z
2026-09-01T13:00:00+03:00
```

Example request:

```http
GET /order/orderlist/admin?page=1&page_size=20&status=pending&create_with=2026-09-01T00:00:00Z
```

## API Endpoints

### Authentication and Users

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/registr` | Public | Register a user |
| POST | `/auth/token` | Public | Receive access and refresh tokens |
| POST | `/token/access` | Refresh token | Receive a new access token |
| GET | `/me` | Authenticated | Get the current user |
| PATCH | `/user/role/{user_id}` | Admin | Change a user role |
| DELETE | `/user/delete/{user_id}` | Owner or admin | Delete an eligible account |

### Categories

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/categories/` | Public | Get active categories |
| GET | `/categories/{category_id}` | Public | Get one active category |
| POST | `/categories/` | Admin | Create a category |
| PATCH | `/categories/{category_id}` | Admin | Update a category |
| DELETE | `/categories/{category_id}` | Admin | Deactivate a category |

### Products

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/products/` | Public | Search, filter, and paginate products |
| GET | `/products/{product_id}` | Public | Get one active product |
| POST | `/products/` | Seller | Create a product |
| PATCH | `/products/{product_id}` | Owner seller | Update a product |
| DELETE | `/products/{product_id}` | Owner seller or admin | Deactivate a product |

### Cart

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/cart/` | Authenticated | Get cart items |
| POST | `/cart/` | Authenticated | Add a product |
| PATCH | `/cart/items/{cart_item_id}` | Owner | Update quantity |
| DELETE | `/cart/items/{cart_item_id}` | Owner | Remove one item |
| DELETE | `/cart/items` | Owner | Clear the cart |

### Orders

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/order/` | Customer | Create an order from the cart |
| GET | `/order/orderlist` | Authenticated | Get the current user's orders |
| GET | `/order/orderlist/admin` | Admin | Get filtered and paginated orders |
| GET | `/order/{order_id}` | Owner | Get one order |
| PATCH | `/order/{order_id}` | Customer or admin | Change an order status |

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/dnndjowow/mini-project-CartFlow-API.git
cd mini-project-CartFlow-API
```

### 2. Create a virtual environment

macOS and Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## PostgreSQL Setup

Connect to PostgreSQL:

```bash
psql -U postgres -d postgres
```

Create a database user:

```sql
CREATE USER cartflow_user WITH PASSWORD 'your_password';
```

Create a database:

```sql
CREATE DATABASE cartflow_db
OWNER cartflow_user
ENCODING 'UTF8';
```

Exit from PostgreSQL:

```sql
\q
```

## Environment Variables

Create `.env` from the provided example:

```bash
cp .env.example .env
```

Configure `.env`:

```env
DATABASE_URL=postgresql+asyncpg://cartflow_user:your_password@localhost:5432/cartflow_db
SECRET_KEY=replace_with_a_long_random_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

The real `.env` file is excluded from Git and must never be committed.

## Database Migrations

Apply all migrations:

```bash
alembic upgrade head
```

Check the current migration:

```bash
alembic current
```

Check whether the models and database schema are synchronized:

```bash
alembic check
```

After changing SQLAlchemy models, create a migration:

```bash
alembic revision --autogenerate -m "describe changes"
```

Apply the new migration:

```bash
alembic upgrade head
```

## Creating the First Administrator

Registration always creates a user with the `customer` role.

Register an account through:

```http
POST /registr
```

Connect to the project database:

```bash
psql -U postgres -d cartflow_db
```

Change the role manually:

```sql
UPDATE users
SET role = 'admin'
WHERE email = 'admin@example.com';
```

Check users:

```sql
SELECT id, email, role
FROM users;
```

After that, the administrator can create categories and assign the `seller` role to other users.

## Running the Application

Start the API from the project root:

```bash
uvicorn app.main:app --reload
```

API address:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

Uploaded images:

```text
http://127.0.0.1:8000/media/products/FILE_NAME
```

## Login Example

The login endpoint uses `OAuth2PasswordRequestForm`.

The registered email must be sent through the `username` field.

```bash
curl -X POST "http://127.0.0.1:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=your_password"
```

Example response:

```json
{
  "access_token": "ACCESS_TOKEN",
  "refresh_token": "REFRESH_TOKEN",
  "token_type": "bearer"
}
```

## Refresh Token Example

```bash
curl -X POST "http://127.0.0.1:8000/token/access" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"REFRESH_TOKEN"}'
```

Example response:

```json
{
  "access_token": "NEW_ACCESS_TOKEN",
  "token_type": "bearer"
}
```

## Product Creation Example

Product creation uses `multipart/form-data`.

```bash
curl -X POST "http://127.0.0.1:8000/products/" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -F "name=Wireless Headphones" \
  -F "descriptions=Bluetooth headphones with noise cancellation" \
  -F "category_id=1" \
  -F "quantity=10" \
  -F "price=199.99" \
  -F "image=@headphones.jpg"
```

## Project Limitations

This is an educational project and is not intended to be a production-ready e-commerce platform.

The current implementation does not include:

- payment gateway integration;
- refresh-token rotation and revocation;
- automatic inclusion of child categories in product filters;
- background image processing;
- cloud file storage;
- email confirmation;
- automated tests;
- structured application logging.

Database rollback does not automatically remove files from the filesystem, so image cleanup is handled separately by the application.

## License

This project was created for educational and portfolio purposes.