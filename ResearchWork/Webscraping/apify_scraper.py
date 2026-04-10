from apify_client import ApifyClient

# Initialize the ApifyClient with your API token
#client = ApifyClient("")
client = ApifyClient("")
# Prepare the Actor input
run_input = {
    "searchUrls": ["https://housing.com/in/buy/mumbai/mira_road_east"],
    "maxItems": 50,
    "proxyConfiguration": {},
}

# Run the Actor and wait for it to finish
run = client.actor("qaKQt1hyMYskNGjck").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)
