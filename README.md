# E-Gadgets

A modern Django-based e-commerce app for gadgets.

- Tech: Django 5, Bootstrap 5, Font Awesome
- Apps: accounts, products, cart, orders, core
- Features: product catalog, categories, wishlist, cart, orders, Razorpay integration

## Local Setup & Deployment

See the detailed steps in [setup.md](./setup.md).

## Environment Variables

Configured via `python-decouple`. Do not commit `.env`.

Required keys (see setup.md for details):
- SECRET_KEY, DEBUG, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS
- EMAIL_* (SMTP)
- RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

## License

Proprietary (update as needed).
