# mini-project-CartFlow-API

CartFlow API is an asynchronous REST API for managing products, shopping carts, and orders. The project demonstrates authentication with JWT, PostgreSQL full-text search, transactional order creation, row-level locking, pagination, filtering, and SQLAlchemy relationships.

## Features

- User registration and authentication
- Access and refresh JWT tokens
- Role-based access control
- Product creation and management
- Soft deletion of products
- PostgreSQL full-text product search
- Product filtering and pagination
- One shopping cart per user
- Adding, updating, and removing cart items
- Transactional order creation
- Automatic stock reduction during checkout
- Stock restoration when an order is cancelled
- Order status transitions
- Row-level locking with `FOR UPDATE`
- Database migrations with Alembic

## Technology Stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- AsyncSession
- asyncpg
- Alembic
- Pydantic 2
- PyJWT
- pwdlib with Argon2
- Uvicorn

## Project Structure

```text
app/
├── migrations/          # Alembic migrations
├── models/              # SQLAlchemy models
├── routers/             # FastAPI endpoints
├── schemas/             # Pydantic schemas
├── auth.py              # Password hashing and JWT functions
├── config.py            # Environment variable configuration
├── database.py          # Async SQLAlchemy engine and session maker
├── db_depends.py        # Database session dependency
├── dependency.py        # Authentication and role dependencies
└── main.py              # FastAPI application
```

## Data Model

The project contains the following main entities:

- `User` — registered user with a role
- `Product` — product created by a seller
- `Cart` — one shopping cart belonging to one user
- `CartItem` — product and quantity stored in a cart
- `Order` — order created from the contents of a cart
- `OrderItem` — product snapshot stored inside an order

### Relationships

```text
User 1 ─── 1 Cart
User 1 ─── M Product
User 1 ─── M Order

Cart 1 ─── M CartItem
Product 1 ─── M CartItem

Order 1 ─── M OrderItem
Product 1 ─── M OrderItem
```

A user can be physically deleted only if they have no products and no orders. Their shopping cart and cart items are deleted automatically.

Products are deleted softly by setting:

```text
is_active = false
```

## User Roles

The API supports the following roles:

- `customer` — default role assigned during registration
- `seller` — can create, update, and deactivate their own products
- `admin` — can change user roles, deactivate any product, view all orders, and manage order statuses

An administrator can change a user role between `customer` and `seller`, provided that the user has no conflicting products or active orders.

## Order Statuses

Available order statuses:

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

A customer can cancel their own order. An administrator can perform the other allowed status transitions.

When an order is cancelled, the ordered quantity is returned to product stock.

## Transaction Safety

Order creation is performed as one database transaction:

1. The user's cart is locked.
2. Cart items are loaded.
3. Products are locked in a stable order.
4. Product availability is checked.
5. An order and order items are created.
6. Product stock is reduced.
7. Cart items are removed.
8. The transaction is committed.

PostgreSQL row-level locking with `FOR UPDATE` protects cart and product data from conflicting concurrent operations.

## Full-Text Search

Products support PostgreSQL full-text search over:

- product name with priority `A`;
- product description with priority `B`.

The search implementation uses:

- generated `TSVECTOR` column;
- `websearch_to_tsquery`;
- `ts_rank_cd`;
- PostgreSQL GIN index;
- relevance-based sorting.

## Product Filtering

`GET /products/` supports:

- `page`
- `page_size`
- `seller_id`
- `search`
- `in_stock`
- `min_price`
- `max_price`

Example:

```http
GET /products/?page=1&page_size=20&search=wireless+headphones&in_stock=true&min_price=50&max_price=500
```

## Order Filtering

The administrator order list supports:

- `page`
- `page_size`
- `order_id`
- `status`
- `create_with`
- `create_up`
- `min_price`
- `max_price`

Example:

```http
GET /order/orderlist/admin?page=1&page_size=20&status=pending&min_price=100
```

## API Endpoints

### Authentication and Users

| Method | Endpoint | Description |
|---|---|---|
| POST | `/registr` | Register a new user |
| POST | `/auth/token` | Authenticate and receive access and refresh tokens |
| POST | `/token/access` | Create a new access token using a refresh token |
| GET | `/me` | Get the current user |
| PATCH | `/user/role/{user_id}` | Change a user role |
| DELETE | `/user/delete/{user_id}` | Physically delete a user without products and orders |

### Products

| Method | Endpoint | Description |
|---|---|---|
| GET | `/products/` | Get products with search, filters, and pagination |
| POST | `/products/` | Create a product |
| GET | `/products/{product_id}` | Get one active product |
| PATCH | `/products/{product_id}` | Update an owned product |
| DELETE | `/products/{product_id}` | Soft-delete a product |

### Cart

| Method | Endpoint | Description |
|---|---|---|
| GET | `/cart/` | Get cart items |
| POST | `/cart/` | Add a product to the cart |
| PATCH | `/cart/items/{cart_item_id}` | Change product quantity |
| DELETE | `/cart/items/{cart_item_id}` | Remove one cart item |
| DELETE | `/cart/items` | Clear the cart |

### Orders

| Method | Endpoint | Description |
|---|---|---|
| POST | `/order/` | Create an order from the cart |
| GET | `/order/orderlist` | Get the current user's orders |
| GET | `/order/orderlist/admin` | Get all orders with filters and pagination |
| GET | `/order/{order_id}` | Get one owned order |
| PATCH | `/order/{order_id}` | Change an order status |

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/dnndjowow/CartFlow-API.git
cd CartFlow-API
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:

```bash
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

Create the database:

```sql
CREATE DATABASE cartflow_db
OWNER cartflow_user
ENCODING 'UTF8';
```

Exit PostgreSQL:

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

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

The real `.env` file is ignored by Git and must not be committed.

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

Create a new migration after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "describe changes"
```

Apply the new migration:

```bash
alembic upgrade head
```

## Creating the First Administrator

Registration creates a user with the `customer` role.

First, register the user through:

```http
POST /registr
```

Then connect to the project database:

```bash
psql -U cartflow_user -d cartflow_db
```

Change the registered user role:

```sql
UPDATE users
SET role = 'admin'
WHERE email = 'admin@example.com';
```

Check the result:

```sql
SELECT id, email, role
FROM users;
```

## Running the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

ReDoc documentation:

```text
http://127.0.0.1:8000/redoc
```

## Authentication

The login endpoint uses `OAuth2PasswordRequestForm`.

When requesting a token:

- enter the email in the `username` field;
- enter the password in the `password` field.

Example:

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

Use the access token in protected requests:

```http
Authorization: Bearer ACCESS_TOKEN
```

Refresh the access token:

```http
POST /token/access
Content-Type: application/json
```

```json
{
  "refresh_token": "REFRESH_TOKEN"
}
```

## License

This project was created for educational and portfolio purposes.