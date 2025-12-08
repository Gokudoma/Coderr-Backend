This repository contains the RESTful API backend for Coderr, a service marketplace application connecting business providers with customers. It is built using Django and Django REST Framework (DRF).



> **Note:** This repository handles the server-side logic, database interactions, and API endpoints.

> **Important:** Do NOT commit the `db.sqlite3` file or `.env` files to GitHub.



## Technologies

* **Python 3.10+**

* **Django 5.x**

* **Django REST Framework (DRF)**

* **SQLite** (Development Database)

* **Pillow** (Image Processing)

* **django-filter** (Advanced Filtering)



## Setup & Installation



1.  **Clone the repository:**

    ```bash

    git clone <YOUR_REPOSITORY_URL>

    cd Coderr-Backend

    ```



2.  **Create and activate virtual environment:**

    * Windows: `python -m venv venv` then `.\venv\Scripts\activate`

    * Mac/Linux: `python3 -m venv venv` then `source venv/bin/activate`



3.  **Install dependencies:**

    ```bash

    pip install -r requirements.txt

    ```



4.  **Environment Configuration:**

    Create a `.env` file in the root directory (next to `manage.py`) and add:

    ```ini

    SECRET_KEY=your-secure-secret-key-here

    DEBUG=True

    ```



5.  **Apply Migrations:**

    ```bash

    python manage.py migrate

    ```



6.  **Create Admin User:**

    To access the Django Admin Panel at `/admin/`, create a superuser:

    ```bash

    python manage.py createsuperuser

    ```



7.  **Run Server:**

    ```bash

    python manage.py runserver

    ```

    The API is now accessible at `http://127.0.0.1:8000/api/`.



## Features

* **Authentication:** Token-based login/register for Customer and Business roles.

* **Profiles:** Detailed user profiles with location, working hours, and images.

* **Offers:** Business users can create service offers with nested packages (Basic/Standard/Premium).

* **Orders:** Purchase system with "Snapshot Logic" to freeze order details at the time of purchase.

* **Reviews:** Rating system allowing customers to review business users.

* **Dashboard:** Statistics for open/completed orders and average ratings.



## Project Structure

The project follows a modular structure (example structure based on features):

* **`coderr/`**: Main settings and routing.

* **`users/`**: Handles authentication and profile logic.

    * `api/`: Contains Serializers, Views, and URLs.

* **`offers/`**: Handles service offers and packages.

    * `api/`: Contains Serializers, Views, and Filtering.

* **`orders/`**: Handles order creation, status workflow, and reviews.



## API Documentation

The API is resource-oriented. Key Examples:

* `POST /api/registration/` - Register a new user

* `POST /api/login/` - Login and retrieve Token

* `GET /api/offers/` - List and filter service offers

* `POST /api/orders/` - Place an order (Customer only)

* `GET /api/base-info/` - Get platform statistics