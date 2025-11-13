# Libraries

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, string, io

# Function to generate captcha
def generate_captcha_text(length=6):
    characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return "".join(random.choice(characters) for _ in range(length))

# Func to generate captcha image
def generate_captcha_image(text):
    width, height = 160, 60
    image = Image.new('RGB',(width,height),(255,255,255))
    draw = ImageDraw.Draw(image)

    try:
        # font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 360)
        font = ImageFont.truetype("arial.ttf",30)
    except Exception as e:
        font = ImageFont.load_default()
    
    '''# Adding noisy lines
    for _ in range(4):
        start = (random.randint(0,width), random.randint(0,height))
        end = (random.randint(0,width), random.randint(0,height))
        draw.line([start,end], fill = (random.randint(100,200), random.randint(100,200), random.randint(100,200)), width=2)
    '''

    # Draw characters, with slight jittered
    for i,ch in enumerate(text):
        x = 12 + i * 22 + random.randint(-2,2)
        y = random.randint(0,12)
        draw.text((x,y), ch, font=font, fill=(random.randint(0,120), random.randint(0,120), random.randint(0,120)))

    # Adding noisy dots
    for _ in range(150):
        draw.point((random.randint(0,width), random.randint(0,height)), fill=(random.randint(0,255), random.randint(0,255), random.randint(0,255)))


    buf = io.BytesIO()
    image.save(buf, format='PNG')
    buf.seek(0)
    return buf
