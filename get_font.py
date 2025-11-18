import requests

def download():
    print("⬇️  Downloading Indie Flower font...")
    # Direct link to the raw TTF file
    url = "https://raw.githubusercontent.com/google/fonts/main/ofl/indieflower/IndieFlower-Regular.ttf"

    r = requests.get(url)
    if r.status_code == 200:
        with open("IndieFlower-Regular.ttf", "wb") as f:
            f.write(r.content)
        print("✅ Success! Font saved as 'IndieFlower-Regular.ttf'")
    else:
        print(f"❌ Failed. Status code: {r.status_code}")

if __name__ == "__main__":
    download()
