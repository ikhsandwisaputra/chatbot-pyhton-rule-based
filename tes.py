from serpapi import GoogleSearch

params = {
  "engine": "google_maps",
  "q": "Coffee",
  "ll": "@40.7455096,-74.0083012,14z",
  "api_key": "915cc566ffd4994a0c3015c69fa63b7539084ced32a4ddc10cc68f95cb78122a"
}

search = GoogleSearch(params)
results = search.get_dict()