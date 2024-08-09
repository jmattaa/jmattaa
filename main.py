import datetime
from dateutil import relativedelta
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

THEME_COLS = {
    'bg': '#282828',  # Background color
    'fg': '#ebdbb2',  # Foreground color
    'black': '#282828',
    'red': '#cc241d',
    'green': '#98971a',
    'yellow': '#d79921',
    'blue': '#458588',
    'purple': '#b16286',
    'cyan': '#689d6a',
    'white': '#a89984',
}

def textsize(text, font):
    im = Image.new(mode="P", size=(0, 0))
    draw = ImageDraw.Draw(im)
    _, _, width, height = draw.textbbox((0, 0), text=text, font=font)
    return width, height

def format_plural(unit): # yeh
    return 's' if unit != 1 else ''
# Returns how old i am 
def age(birthday):
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} {}, {} {}, {} {}{}'.format(
        diff.years, 'year' + format_plural(diff.years), 
        diff.months, 'month' + format_plural(diff.months), 
        diff.days, 'day' + format_plural(diff.days),
        ' 🎂' if (diff.months == 0 and diff.days == 0) else '')

# Function to fetch GitHub data
def fetch_github_data(username):
    try:
        url = f"https://api.github.com/users/{username}"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        return {
            'name': data.get('name', 'N/A'),
            'public_repos': data.get('public_repos', 'N/A'),
            'followers': data.get('followers', 'N/A'),
            'following': data.get('following', 'N/A')
        }
    except requests.RequestException as e:
        print(f"Error fetching GitHub data: {e}")
        return {
            'name': 'N/A',
            'public_repos': 'N/A',
            'followers': 'N/A',
            'following': 'N/A'
        }

# Function to load ASCII art from a file
def load_ascii_art(filename):
    try:
        with open(filename, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        return ""

def draw_highlighted_text(draw, position, text, font, fontsize, theme_cols):
    left_side_color = theme_cols['yellow']
    semicolon_color = theme_cols['white']
    right_side_color = theme_cols['cyan']

    x, y = position

    for line in text.split('\n'):
        # Split the line at the semicolon
        parts = line.split(':')
        
        if len(parts) == 2:  
            left_text = parts[0]
            right_text = parts[1]
            draw.text((x, y), left_text, font=font, fill=left_side_color)
            x += textsize(left_text, font=font)[0]
            
            draw.text((x, y), ':', font=font, fill=semicolon_color)
            x += textsize(':', font=font)[0]
            
            draw.text((x, y), right_text, font=font, fill=right_side_color)
        elif line.startswith("    "):
            draw.text((x, y), line, font=font, fill=right_side_color)
        else:
            # If there's no semicolon, just draw the text normally
            draw.text((x, y), line, font=font, fill=theme_cols['fg'])

        y += fontsize
        x = position[0]

def create_image_with_stats(ascii_art_filename, username):
    # Fetch GitHub data
    stats = fetch_github_data(username)

    # Load ASCII art
    ascii_art = load_ascii_art(ascii_art_filename)
    
    # Settings
    img_width = 1400
    img_height = 700 
    ascii_font_size = 9.3333333333 # it's 150 chars wide do some math
    stats_font_size = 20   # Larger font size for GitHub stats
    ascii_art_width = img_width // 2
    font_path = "./res/DejaVuSansMono.ttf"

    # Create a new image with Gruvbox background color
    img = Image.new('RGB', (img_width, img_height), color=THEME_COLS['bg'])
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        ascii_font = ImageFont.truetype(font_path, ascii_font_size)
        stats_font = ImageFont.truetype(font_path, stats_font_size)
    except IOError:
        print(f"Error: Font file {font_path} not found.")
        return

    # Create an image from the ASCII art
    ascii_art_image = Image.new('RGB', (ascii_art_width, img_height), color=THEME_COLS['bg'])
    ascii_draw = ImageDraw.Draw(ascii_art_image)
    
    # Split ASCII art into lines and draw on the image
    y_position = 0
    for line in ascii_art.splitlines():
        ascii_draw.text((0, y_position), line, fill=THEME_COLS['fg'], font=ascii_font)
        y_position += ascii_font_size
    
    # Resize ASCII art image to fit
    ascii_art_image = ImageOps.fit(ascii_art_image, (ascii_art_width, img_height), method=Image.Resampling.BOX)

    # Paste ASCII art image onto the final image
    img.paste(ascii_art_image, (0, 0))

    language_stats = {}
    total_bytes = 0
    total_stars = 0

    repos_response = requests.get(f"https://api.github.com/users/{username}/repos")
    repos = repos_response.json()

    for repo in repos:
        if not repo['fork']:  # Skip forked repositories
            lang_response = requests.get(repo['languages_url'])
            languages = lang_response.json()
            total_stars += repo['stargazers_count']  # Add stars to the total

            for lang, bytes in languages.items():
                total_bytes += bytes
                if lang in language_stats:
                    language_stats[lang] += bytes
                else:
                    language_stats[lang] = bytes

    # Convert to percentage
    language_percentage = {lang: (bytes / total_bytes) * 100 for lang, bytes in language_stats.items()}
    sorted_languages = sorted(language_percentage.items(), key=lambda x: x[1], reverse=True)[:6] # get top 6
    formatted_languages = "\n".join(f"    {lang} ({percentage:.2f})" for lang, percentage in sorted_languages)

    top_repos = sorted(repos, key=lambda x: x['stargazers_count'], reverse=True)[:3] # only get 3
    formatted_top_repos = "\n".join(f"    {name} ({stars} stars)" for repo in top_repos for name, stars in [(repo['name'], repo['stargazers_count'])])

    # Draw GitHub stats on the right side
    text = (
        f"jonathan@{username}\n"
        "------------\n"
        f"OS: Arch (btw)\n"
        f"Uptime: {age(datetime.datetime(2007, 8, 18))}\n"
        "\n"
        "Hobbies: [Talking, Music, Gym, Vim]\n"
        "Editor: neovim\n"
        "\n"
        "Github Stats:\n"
        "------------\n"
        f"Github.public_repos: {stats['public_repos']}\n"
        f"Github.followers: {stats['followers']}\n"
        f"Github.following: {stats['following']}\n"
        f"Github.stars_recieved: {total_stars}\n"
        "\n"
        "Github.languages:\n"
        f"{formatted_languages}\n"
        "\n"
        "Github.top_repos: \n"
        f"{formatted_top_repos}\n"
    )

    draw_highlighted_text(draw, (ascii_art_width + 20, 20), text, stats_font, stats_font_size, THEME_COLS)

    # Save the image
    img.save('img.png')

create_image_with_stats('./res/me.txt', 'jmattaa')


