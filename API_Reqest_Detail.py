import requests
import time
import csv
from geopy.distance import geodesic

api_key = "AIzaSyCj3pyZjWziZUdriwNg78znHb2QkN7sMHc"  # Replace with your actual API key
address = "Germaniastraße 17 Munich Germany"

def get_location(api_key, address):
    """Geocode address to get latitude and longitude."""
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}
    response = requests.get(geocode_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
    return None, None

def get_latest_review(api_key, place_id):
    """Fetch the latest review for a place using the Google Places API."""
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": api_key,
        "fields": "reviews"
    }
    response = requests.get(details_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("result", {}).get("reviews"):
            latest_review = data["result"]["reviews"][0]["text"]  # Assuming the first review is the latest
            return latest_review
    return "No reviews found"

def find_restaurants(api_key, latitude, longitude, min_rating=4.6, radius=1000):
    """Find restaurants using the Google Places API."""
    places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{latitude},{longitude}",
        "radius": radius,
        "type": "restaurant",
        "minprice": min_rating,
        "key": api_key
    }
    restaurants = []
    while True:
        response = requests.get(places_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "OK":
                for place in data["results"]:
                    if place.get("rating", 0) >= min_rating:
                        restaurant_lat = place["geometry"]["location"]["lat"]
                        restaurant_lng = place["geometry"]["location"]["lng"]
                        distance = geodesic((latitude, longitude), (restaurant_lat, restaurant_lng)).meters
                        review = get_latest_review(api_key, place["place_id"])
                        restaurants.append({
                            "name": place["name"],
                            "rating": place.get("rating", "No rating"),
                            "type": ", ".join([x for x in place.get("types", []) if x != "restaurant"]),
                            "distance": distance,
                            "latest_review": review  # Add latest review to the restaurant info
                        })
                if "next_page_token" in data:
                    params['pagetoken'] = data['next_page_token']
                    time.sleep(2)
                else:
                    break
            else:
                break
        else:
            break

    # Sort the restaurants by distance
    restaurants.sort(key=lambda x: x['distance'])
    return restaurants

def save_results_to_csv(restaurants, filename='restaurants.csv'):
    """Save the restaurant data to a CSV file."""
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['name', 'rating', 'type', 'distance', 'latest_review'])
        writer.writeheader()
        for restaurant in restaurants:
            writer.writerow(restaurant)
    print(f"Results saved to {filename}")

# Main script execution
latitude, longitude = get_location(api_key, address)
if latitude is not None and longitude is not None:
    restaurants = find_restaurants(api_key, latitude, longitude)
    save_results_to_csv(restaurants)  # Save the results to a CSV file instead of displaying in a pop-up window
else:
    print("Failed to get location coordinates.")
