# Anime Web Crawler

A powerful, asynchronous web crawler designed to scrape anime details and fetch episode embed links.

## Features
- **Scrape Anime List**: Crawls the AZ-list to gather anime titles and slugs.
- **Fetch Episode Links**: Iterates through episodes to find all available iframe/embed URLs.
- **Resumable**: Both scripts support resuming execution if interrupted, skipping already processed items.
- **Incremental Saving**: Data is saved to CSV immediately after processing each item.

## Prerequisites
- **Python 3.9+**
- **Git**

## Installation

This project is designed to run in an **isolated environment**. You do **not** need to install dependencies or browsers system-wide. Everything is contained within the project folder (and your user's cache).

### 1. System Setup (Distro Specific)

**Debian / Ubuntu / Kali**
```bash
sudo apt update
sudo apt install python3 python3-venv git
```

**Arch Linux / Manjaro**
```bash
sudo pacman -S python git
```

**Fedora**
```bash
sudo dnf install python3 git
```

**macOS** (using Homebrew)
```bash
brew install python git
```

**Windows**
- Install [Python](https://www.python.org/downloads/) (Check "Add Python to PATH")
- Install [Git](https://git-scm.com/download/win)

### 2. Project Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Kapy2003/web-crawler-custom.git
   cd web-crawler-custom
   ```

### 2. Project Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Kapy2003/web-crawler-custom.git
   cd web-crawler-custom
   ```

2. **Create and Activate Virtual Environment**:

   #### 🐧 Linux / 🍎 macOS
   ```bash
   # Create (.venv folder)
   python3 -m venv .venv
   
   # Activate
   source .venv/bin/activate
   ```

   #### 🪟 Windows (PowerShell / CMD)
   ```powershell
   # Create
   python -m venv .venv
   
   # Activate
   .venv\Scripts\activate
   ```
   *Note: If you get a permission error on PowerShell, run the following command:*
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install the isolated browser**:
   This downloads a local Chromium binary to your user cache.
   - **Linux/macOS**: `~/.cache/ms-playwright/`
   - **Windows**: `%USERPROFILE%\AppData\Local\ms-playwright`

   ```bash
   playwright install chromium
   ```

## Configuration

1. Create a `.env` file in the root directory (optional if relying on defaults):
   ```bash
   touch .env
   ```

2. Add environment variables if needed (e.g., custom configuration):
   ```env
   # Example
   # HEADLESS=true
   ```

## Usage

### Phase 1: Scraping the Anime List
Run the main list scraper to populate the database of animes.

```bash
python main_az_list.py
```
- **Output**: Generates `anime_az_list.csv`.
- **Behavior**: Scrapes pages sequentially. If interrupted, simply run it again; it will automatically skip already saved animes.

### Phase 2: Fetching Episode Links
Once you have the list, run the iframe fetcher to get the episode video links.

```bash
python fetch_iframes.py
```
- **Input**: Reads `anime_az_list.csv`.
- **Output**: Generates `anime_az_list_with_iframes.csv`.
- **Behavior**:
    - Fetches all available episodes for each anime (loops until no episode is found).
    - Stores links in the `embed_url` column as a JSON string: `{"1": "url1", "2": "url2"}`.
    - If interrupted, run it again to resume.

## Output Format
The `embed_url` column in the final CSV is a JSON object mapping episode numbers to their source URLs.
Example:
```json
{
  "1": "https://example.com/embed/ep1",
  "2": "https://example.com/embed/ep2"
}
```
