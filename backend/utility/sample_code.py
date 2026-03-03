import os
from google import genai
from google.genai.types import RecontextImageSource, ProductImage, Image

# 1. Configuration
PROJECT_ID = "YOUR_PROJECT_ID"
LOCATION = "us-central1" # Or your specific region
API_KEY = "YOUR_API_KEY"

# 2. Initialize Client
# While Service Accounts are recommended, you can use the API key for quick testing
client = genai.Client(
    api_key=API_KEY,
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

def run_virtual_try_on(person_path, product_path, output_path="result.png"):
    try:
        # 3. Call the Virtual Try-On model
        response = client.models.recontext_image(
            model="virtual-try-on-001",
            source=RecontextImageSource(
                person_image=Image.from_file(location=person_path),
                product_images=[
                    ProductImage(product_image=Image.from_file(location=product_path))
                ],
            ),
        )

        # 4. Save the generated image
        if response.generated_images:
            response.generated_images[0].image.save(output_path)
            print(f"Success! Saved try-on result to: {output_path}")
        else:
            print("No image was generated.")

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the test
if __name__ == "__main__":
    run_virtual_try_on("person.jpg", "shirt.jpg")
