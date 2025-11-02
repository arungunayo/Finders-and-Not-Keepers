# Finders-and-Not-Keepers

A community-driven lost and found platform that helps people reunite with their lost belongings. Built with FastAPI, PostgreSQL, and powered by AI-driven categorization.

Made for OpenVerse - Hack Night(mare) 🎃

## Features

- **Report Lost Items**: Users can report items they've lost with detailed descriptions and images
- **Report Found Items**: Community members can report items they've found to help return them
- **Smart Search**: Search through reported items by name, location, or description
- **AI-Powered Tagging**: Automatic categorization of items using Hugging Face's zero-shot classification
- **Image Upload**: Cloudinary integration for secure image hosting
- **Detailed Item Views**: View comprehensive information about each reported item
- **Contact Information**: Direct contact details to facilitate item returns

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL (Neon)
- **Image Storage**: Cloudinary
- **AI/ML**: Hugging Face Inference API (BART-large-MNLI for zero-shot classification)
- **Frontend**: HTML, Tailwind CSS, Jinja2 Templates
- **Validation**: Pydantic

## Prerequisites

- Python 3.8+
- PostgreSQL database (or Neon serverless Postgres)
- Cloudinary account
- Hugging Face API key

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/arungunayo/Finders-and-Not-Keepers.git
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install fastapi uvicorn psycopg2-binary cloudinary python-dotenv pydantic huggingface-hub requests python-multipart jinja2
```
Or
```bash
pip install -r "requirements.txt"
```

4. **Set up environment variables**

Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://user:password@host:port/database
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
HUGGINGFACE_API_KEY=your_hf_api_key
```

5. **Initialize the database**

The database table will be created automatically when you run the application for the first time.

## Running the Application

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at `http://localhost:8000`

## Project Structure

```
lost-and-found/
├── main.py                 # Main application file
├── templates/              # HTML templates
│   ├── home.html          # Landing page
│   ├── report_form.html   # Form for reporting items
│   ├── items.html         # Browse all items
│   └── item_detail.html   # Individual item details
├── .env                   # Environment variables (not in repo)
└── README.md             # This file
```

## API Endpoints

### Template Routes
- `GET /` - Home page
- `GET /report-lost` - Report a lost item form
- `GET /report-found` - Report a found item form
- `GET /view-items?search=query` - Browse all items with optional search
- `GET /item/{item_id}` - View detailed information about a specific item

### Form Submission
- `POST /submit-item` - Submit a new lost or found item report

## Features in Detail

### AI-Powered Categorization

The application uses Hugging Face's BART-large-MNLI model for zero-shot classification to automatically categorize items into the following tags:

- Electronics
- Clothing & Accessories
- Documents & Books
- Sports Equipment & Toys
- Personal Items (wallets, bags, jewelry, watches, glasses)
- Identification (ID cards, credit cards, passports)
- Academic/Work Items (laptops, notebooks, stationery)
- Transport Items (bicycles, helmets, keys)
- Miscellaneous

### Image Upload

Images are securely uploaded to Cloudinary and stored in the `lost_and_found/` folder. The secure URL is then saved in the database.

### Database Schema

```sql
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(20) NOT NULL,        -- 'lost' or 'found'
    item_name VARCHAR(100) NOT NULL,
    description TEXT,
    location VARCHAR(255) NOT NULL,
    contact_info VARCHAR(100) NOT NULL,
    image_path TEXT,
    tag VARCHAR(50),                       -- Auto-generated category
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `CLOUDINARY_CLOUD_NAME` | Your Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `HUGGINGFACE_API_KEY` | Hugging Face API token |

## Development

### Adding New Categories

To add new item categories, modify the `labels` list in the `auto_tag_item()` function in `main.py`:

```python
labels = [
    "electronics", "clothing", "accessories",
    # Add your new categories here
    "your_new_category"
]
```

### Customizing the UI

The templates use Tailwind CSS via CDN. Modify the HTML files in the `templates/` directory to customize the look and feel.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Hugging Face for the zero-shot classification model
- Cloudinary for image hosting
- FastAPI for the amazing web framework
- Tailwind CSS for the styling framework

## Support

For issues or questions, please open an issue on the GitHub repository.

---

Made with ❤️ to help people reconnect with their belongings by Arungunayo and Akio-1 (AFK Bros)
