#Book Scraper

Scrape the web to get infos about books. 
This webapp has been planned and implemented to get published books informations not yet available on Google Books APIs.

Built on top of Muffin Framework, it exposes just one endpoint to retrieve info about a specific book, identified by its own ISBN. 
It uses the new *asyncio* module to retrieve infos by two (for now) providers.

##Run locally

- virtualenv --distribute -p /usr/bin/where/is/python34 book_scraper
- cd book_scraper
- git clone git@github.com:brunifrancesco/bookInfoScraper.git
- source bin/activate
- cd book_scraper
- pip install -r requirements.txt
- muffin server run
- curl http://localhost:5000/scrape?isbn=9788858109779
