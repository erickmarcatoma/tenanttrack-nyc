from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.i18n.dates import format_date

templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")
templates.env.filters["fdate"] = format_date
