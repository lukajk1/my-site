from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import requests

# 1. Initialize the model and processor
# Using the 'base' model is a good balance for speed and quality.
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# 2. Prepare the image
# You can use a local file path, or fetch an image from a URL
img_url = 'https://storage.googleapis.com/sfr-vision-language-research/BLIP/demo.jpg'
raw_image = Image.open(requests.get(img_url, stream=True).raw).convert('RGB')

# If you have a local image, use:
# raw_image = Image.open("path/to/your/image.jpg").convert('RGB')

# 3. Process the image for the model
# The processor handles resizing and normalization.
inputs = processor(raw_image, return_tensors="pt")

# 4. Generate the caption
# 'max_length' controls the length of the generated caption.
out = model.generate(**inputs, max_length=50)

# 5. Decode and print the result
caption = processor.decode(out[0], skip_special_tokens=True)

print(f"Generated Caption: {caption}")
