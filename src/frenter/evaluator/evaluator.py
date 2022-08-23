import json
from frenter.datasets.postcode_dataset import PostcodeDataset
from frenter.scrappers.zoopla_scrapper import ZooplaScrapper
from frenter.scrappers.crystalroof_scrapper import CrystalRoofScrapper


class Evaluator:

    def __init__(
            self,
            filter_params,
            state_path: str,
            postcode_dataset_path: str,
            loop_timeout: int = 5,
            pages_amount: int = 10,
    ):
        self.filter_params = filter_params
        self.state_path = state_path
        self.loop_timeout = loop_timeout
        self.pages_amount = pages_amount

        self.state = None
        self._load_state()
        self.postcode_dataset = PostcodeDataset(postcode_dataset_path)
        self.property_scrapper = ZooplaScrapper()
        self.metadata_scrapper = CrystalRoofScrapper()

    def _load_state(self):
        with open(self.state_path, "r") as f:
            self.state = json.load(f)

    def _save_state(self):
        with open(self.state_path, "w") as f:
            json.dump(self.state, f)

    def _filter_listing(self, listing_id: int):

        if listing_id in self.state["listing_ids"]:
            return None

        listing = self.property_scrapper.get_listing_details(listing_id)
        postcode = self.postcode_dataset.find_postcode_by_coordinate(
            latitude=listing["location"]["coordinates"]["latitude"],
            longitude=listing["location"]["coordinates"]["longitude"]
        )
        transport = self.metadata_scrapper.get_transport(postcode)
        if transport["zone"] > self.filter_params["zone"]:
            return None

        listing["postcode"] = postcode

        return listing

    def _get_listing_report(self, listing):
        postcode = listing["postcode"]
        crime_rate = self.metadata_scrapper.get_crime(postcode)
        rate, main_demographics_group = self.metadata_scrapper.get_main_demographics_group(postcode)

        return {
            "crime_rate": crime_rate,
            "main_demographics_group": main_demographics_group,
        }

    def _step(self):
        listings = []
        for i in range(self.pages_amount):
            listing_short = self.property_scrapper.get_listings_page(
                page_number=i,
                price_min=self.filter_params["price_min"],
                price_max=self.filter_params["price_max"],
                furnished_state=self.filter_params["furnished_state"],
                beds_num=self.filter_params["beds_num"],
            )
            listing = self._filter_listing(listing_short["listingId"])
            if listing:
                listings.append(listing)
        pass
