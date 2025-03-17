import os
import io
import requests
from PIL import Image, ImageDraw, ImageFont
import imageio
from typing import Dict, Any, List, Tuple, Optional
import random
import numpy as np
import time
import json
from functools import lru_cache

# Simple file-based cache for PokeAPI responses
CACHE_DIR = os.path.join(os.environ.get("TEMP_DIR", "/tmp"), "pokeapi_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cached_data(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Get cached data for a given cache key
    
    Args:
        cache_key: Cache key to retrieve
        
    Returns:
        Cached data or None if not found
    """
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_cached_data(cache_key: str, data: Dict[str, Any]) -> None:
    """
    Save data to cache
    
    Args:
        cache_key: Cache key to save under
        data: Data to cache
    """
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    try:
        with open(cache_file, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def get_cached_image(cache_key: str) -> Optional[Image.Image]:
    """
    Get cached image for a given cache key
    
    Args:
        cache_key: Cache key to retrieve
        
    Returns:
        Cached PIL Image or None if not found
    """
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.png")
    if os.path.exists(cache_file):
        try:
            return Image.open(cache_file)
        except Exception:
            return None
    return None

def save_cached_image(cache_key: str, img: Image.Image) -> None:
    """
    Save image to cache
    
    Args:
        cache_key: Cache key to save under
        img: PIL Image to cache
    """
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.png")
    try:
        img.save(cache_file, "PNG")
    except Exception:
        pass

def get_pokemon_data(pokemon_name: str) -> Dict[str, Any]:
    """
    Get Pokémon data from the PokéAPI with caching
    
    Args:
        pokemon_name: Name of the Pokémon
        
    Returns:
        Dictionary containing Pokémon data
    """
    # Normalize the Pokémon name for consistent caching
    pokemon_name = pokemon_name.lower().replace(" ", "-").replace(".", "").replace("'", "")
    
    # Check cache first
    cache_key = f"pokemon_{pokemon_name}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data
    
    # If not in cache, fetch from API
    try:
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Cache the data
        save_cached_data(cache_key, data)
        return data
    except Exception as e:
        print(f"Error fetching Pokemon data for {pokemon_name}: {str(e)}")
        # Return minimal data structure to avoid downstream errors
        return {
            "name": pokemon_name,
            "sprites": {
                "front_default": None,
                "other": {
                    "official-artwork": {
                        "front_default": None
                    }
                }
            }
        }

def get_pokemon_sprite(pokemon_name: str, sprite_variant: str = "default", is_first_pokemon: bool = False) -> Image.Image:
    """
    Get a Pokémon sprite from the PokéAPI with caching
    
    Args:
        pokemon_name: Name of the Pokémon
        sprite_variant: Sprite variant to use (default, female, shiny, shiny_female)
        is_first_pokemon: Whether this is the first Pokémon (uses back sprite if True)
        
    Returns:
        PIL Image object of the Pokémon sprite
    """
    # Normalize the Pokémon name for consistent caching
    pokemon_name = pokemon_name.lower().replace(" ", "-").replace(".", "").replace("'", "")
    
    # Define the sprite side (back for first Pokémon, front for second)
    sprite_side = "back" if is_first_pokemon else "front"
    
    # Check sprite cache first
    cache_key = f"sprite_{pokemon_name}_{sprite_side}_{sprite_variant}"
    cached_sprite = get_cached_image(cache_key)
    if cached_sprite:
        return cached_sprite
    
    try:
        # First try to get the form data which has better sprite options
        form_data = get_pokemon_form_data(pokemon_name)
        data = get_pokemon_data(pokemon_name)
        
        # Try different sprite sources in order of preference
        sprite_url = None
        
        # Determine the appropriate sprite URL based on variant and whether it's the first Pokemon
        if is_first_pokemon:
            # For the first Pokémon, we want the back sprite
            if sprite_variant == "female" and "back_female" in data["sprites"] and data["sprites"]["back_female"]:
                sprite_url = data["sprites"]["back_female"]
            elif sprite_variant == "shiny" and "back_shiny" in data["sprites"] and data["sprites"]["back_shiny"]:
                sprite_url = data["sprites"]["back_shiny"]
            elif sprite_variant == "shiny_female" and "back_shiny_female" in data["sprites"] and data["sprites"]["back_shiny_female"]:
                sprite_url = data["sprites"]["back_shiny_female"]
            elif "back_default" in data["sprites"] and data["sprites"]["back_default"]:
                sprite_url = data["sprites"]["back_default"]
            else:
                # If no back sprite is available, fall back to front sprite
                sprite_url = data["sprites"]["front_default"]
        else:
            # For the second Pokémon or if not first Pokemon specified, use front sprites
            if form_data and "sprites" in form_data:
                sprites = form_data["sprites"]
                
                # Select the appropriate sprite based on the variant
                if sprite_variant == "female" and sprites.get("front_female"):
                    sprite_url = sprites["front_female"]
                elif sprite_variant == "shiny" and sprites.get("front_shiny"):
                    sprite_url = sprites["front_shiny"]
                elif sprite_variant == "shiny_female" and sprites.get("front_shiny_female"):
                    sprite_url = sprites["front_shiny_female"]
                else:
                    # Default to front_default
                    sprite_url = sprites.get("front_default")
            else:
                # Fall back to standard sprites if form data is not available
                # Try official artwork first, then standard sprite
                if data["sprites"]["other"]["official-artwork"]["front_default"]:
                    sprite_url = data["sprites"]["other"]["official-artwork"]["front_default"]
                elif "home" in data["sprites"]["other"] and data["sprites"]["other"]["home"]["front_default"]:
                    sprite_url = data["sprites"]["other"]["home"]["front_default"]
                elif data["sprites"]["front_default"]:
                    sprite_url = data["sprites"]["front_default"]
            
        if sprite_url:
            # Get the sprite image
            response = requests.get(sprite_url)
            response.raise_for_status()
            
            # Convert to PIL Image
            sprite = Image.open(io.BytesIO(response.content))
            
            # Ensure transparency
            if sprite.mode != 'RGBA':
                sprite = sprite.convert('RGBA')
            
            # Create a mask for the sprite to maintain transparency
            # This helps eliminate any black backgrounds
            # Pixels with RGB values close to black are made transparent
            data = sprite.getdata()
            new_data = []
            
            # Check if the image already has transparency
            has_transparency = sprite.mode == 'RGBA' and any(item[3] < 255 for item in data)
            
            # Only process if the image doesn't already have transparency
            if not has_transparency:
                # Check outer edges for background color (usually black in Pokemon sprites)
                width, height = sprite.size
                edge_pixels = []
                
                # Sample pixels from the edges of the image
                for x in range(width):
                    edge_pixels.append(data[x])  # Top edge
                    edge_pixels.append(data[(height-1) * width + x])  # Bottom edge
                
                for y in range(height):
                    edge_pixels.append(data[y * width])  # Left edge
                    edge_pixels.append(data[y * width + width - 1])  # Right edge
                
                # Count black and near-black pixels on the edges
                bg_color_count = sum(1 for p in edge_pixels if p[0] < 10 and p[1] < 10 and p[2] < 10)
                
                # If most edge pixels are black, we should remove the black background
                if bg_color_count > len(edge_pixels) * 0.7:
                    for item in data:
                        # More conservative approach: only make pixels transparent if they're very black
                        # and based on alpha if available
                        if item[0] < 10 and item[1] < 10 and item[2] < 10:
                            # Very black pixel - make transparent
                            new_data.append((0, 0, 0, 0))
                        else:
                            # Keep the original pixel
                            new_data.append(item)
                    sprite.putdata(new_data)
                # Otherwise, keep the image as is (it likely has intended black parts)
            
            # Resize to a reasonable size (preserve aspect ratio)
            sprite.thumbnail((400, 400), Image.LANCZOS)
            
            # Cache the processed sprite
            save_cached_image(cache_key, sprite)
            
            return sprite
    except Exception as e:
        print(f"Error fetching sprite for {pokemon_name}: {str(e)}")
    
    # Return a placeholder image for errors
    placeholder = Image.new('RGBA', (200, 200), (255, 255, 255, 0))
    draw = ImageDraw.Draw(placeholder)
    draw.text((30, 90), f"No sprite for\n{pokemon_name}", fill=(0, 0, 0))
    return placeholder

def get_pokemon_form_data(pokemon_name: str) -> Dict[str, Any]:
    """
    Get Pokémon form data from the PokéAPI with caching
    
    Args:
        pokemon_name: Name of the Pokémon
        
    Returns:
        Dictionary containing Pokémon form data
    """
    # Normalize the Pokémon name for consistent caching
    pokemon_name = pokemon_name.lower().replace(" ", "-").replace(".", "").replace("'", "")
    
    # Check cache first
    cache_key = f"pokemon_form_{pokemon_name}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data
    
    # If not in cache, fetch from API
    try:
        url = f"https://pokeapi.co/api/v2/pokemon-form/{pokemon_name}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Cache the data
        save_cached_data(cache_key, data)
        return data
    except Exception as e:
        print(f"Error fetching Pokemon form data for {pokemon_name}: {str(e)}")
        return None

def create_health_bar(health_percentage: float, width: int = 100, height: int = 10) -> Image.Image:
    """
    Create a health bar image
    
    Args:
        health_percentage: Health percentage (0.0 to 1.0)
        width: Width of the health bar
        height: Height of the health bar
        
    Returns:
        PIL Image of the health bar
    """
    bar = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bar)
    
    # Draw border
    draw.rectangle([(0, 0), (width-1, height-1)], outline=(0, 0, 0))
    
    # Draw health
    health_width = max(1, int(width * health_percentage))  # Ensure minimum width of 1 pixel
    if health_percentage > 0.5:
        color = (0, 255, 0)  # Green
    elif health_percentage > 0.2:
        color = (255, 255, 0)  # Yellow
    else:
        color = (255, 0, 0)  # Red
    
    # Only draw the health rectangle if there's any health left
    if health_percentage > 0:
        draw.rectangle([(1, 1), (health_width - 1, height - 2)], fill=color)
    
    return bar

def create_battle_frame(
    pokemon1_sprite: Image.Image,
    pokemon2_sprite: Image.Image,
    pokemon1_name: str,
    pokemon2_name: str,
    pokemon1_health: float,
    pokemon2_health: float,
    message: str = ""
) -> Image.Image:
    """
    Create a battle frame
    
    Args:
        pokemon1_sprite: Sprite of the first Pokémon
        pokemon2_sprite: Sprite of the second Pokémon
        pokemon1_name: Name of the first Pokémon
        pokemon2_name: Name of the second Pokémon
        pokemon1_health: Health percentage of the first Pokémon (0.0 to 1.0)
        pokemon2_health: Health percentage of the second Pokémon (0.0 to 1.0)
        message: Battle message to display
        
    Returns:
        PIL Image of the battle frame
    """
    # Create a new image with a gradient background for more visual appeal
    frame = Image.new('RGB', (800, 500), (240, 248, 255))
    draw = ImageDraw.Draw(frame)
    
    # Create a gradient background
    for y in range(500):
        # Create a blue to light blue gradient
        r = int(176 + (y / 500) * 64)
        g = int(224 + (y / 500) * 31)
        b = int(230 + (y / 500) * 25)
        for x in range(800):
            draw.point((x, y), fill=(r, g, b))
    
    # Draw a simple battle field
    # Green ground
    draw.rectangle([(0, 380), (800, 500)], fill=(76, 187, 23))
    
    # Draw dividing line
    draw.line([(0, 380), (800, 380)], fill=(50, 50, 50), width=2)
    
    # Add some details to the battlefield
    # Add small circles for decoration
    for i in range(10):
        x = random.randint(50, 750)
        y = random.randint(400, 480)
        size = random.randint(5, 15)
        color = (random.randint(50, 100), random.randint(160, 200), random.randint(20, 50))
        draw.ellipse([(x-size, y-size), (x+size, y+size)], fill=color)
    
    # Load a font (using default if custom font fails)
    try:
        font = ImageFont.truetype("arial.ttf", 22)
        small_font = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Add a platform for each Pokémon
    # Platform for Pokémon 1
    platform1_x = 200  # Moved more to the left
    platform1_y = 340  # Slightly higher on battlefield
    
    # Platform for Pokémon 2
    platform2_x = 600  # Keep this position
    platform2_y = 290  # Slightly higher on battlefield
    
    # Draw Pokémon sprites with shadows
    # Shadow for Pokémon 1
    shadow1 = create_pokemon_shadow(pokemon1_sprite)
    # Position the shadow at the bottom of where the sprite will be
    shadow1_pos_x = platform1_x - shadow1.width//2
    shadow1_pos_y = platform1_y - 5  # Place shadow on the ground
    frame.paste(shadow1, (shadow1_pos_x, shadow1_pos_y), shadow1)
    
    # Shadow for Pokémon 2
    shadow2 = create_pokemon_shadow(pokemon2_sprite)
    # Position the shadow at the bottom of where the sprite will be
    shadow2_pos_x = platform2_x - shadow2.width//2
    shadow2_pos_y = platform2_y - 5  # Place shadow on the ground
    frame.paste(shadow2, (shadow2_pos_x, shadow2_pos_y), shadow2)
    
    # Calculate vertical offset based on sprite height - larger sprites need more offset
    pokemon1_y_offset = int(pokemon1_sprite.height / 2.5)  # Using regular division then converting to int
    pokemon2_y_offset = int(pokemon2_sprite.height / 2.5)  # Using regular division then converting to int
    
    # Pokemon 1 (left side) - Ensure it's directly centered over the shadow
    pokemon1_pos_x = platform1_x - pokemon1_sprite.width//2  # Center on platform
    pokemon1_pos_y = platform1_y - pokemon1_sprite.height + pokemon1_y_offset
    frame.paste(pokemon1_sprite, (pokemon1_pos_x, pokemon1_pos_y), pokemon1_sprite)
    
    # Pokemon 2 (right side) - Position directly above shadow center
    pokemon2_pos_x = platform2_x - pokemon2_sprite.width//2  # Center on platform
    pokemon2_pos_y = platform2_y - pokemon2_sprite.height + pokemon2_y_offset
    frame.paste(pokemon2_sprite, (pokemon2_pos_x, pokemon2_pos_y), pokemon2_sprite)
    
    # Create nicer name displays with health bars
    # Name display for Pokémon 1
    name_bg1 = Image.new('RGBA', (180, 70), (255, 255, 255, 180))
    name_draw1 = ImageDraw.Draw(name_bg1)
    name_draw1.rectangle([(0, 0), (179, 69)], outline=(0, 0, 0))
    name_draw1.text((10, 10), pokemon1_name.capitalize(), fill=(0, 0, 0), font=font)
    
    # Health bar for Pokémon 1
    health_bar1 = create_health_bar(pokemon1_health, width=160)
    name_bg1.paste(health_bar1, (10, 40), health_bar1)
    frame.paste(name_bg1, (50, 50), name_bg1)
    
    # Name display for Pokémon 2
    name_bg2 = Image.new('RGBA', (180, 70), (255, 255, 255, 180))
    name_draw2 = ImageDraw.Draw(name_bg2)
    name_draw2.rectangle([(0, 0), (179, 69)], outline=(0, 0, 0))
    name_draw2.text((10, 10), pokemon2_name.capitalize(), fill=(0, 0, 0), font=font)
    
    # Health bar for Pokémon 2
    health_bar2 = create_health_bar(pokemon2_health, width=160)
    name_bg2.paste(health_bar2, (10, 40), health_bar2)
    frame.paste(name_bg2, (550, 50), name_bg2)
    
    # Draw battle message in a more appealing dialog box
    max_width = 60  # characters per line
    lines = []
    for i in range(0, len(message), max_width):
        lines.append(message[i:i+max_width])
    
    message_box = Image.new('RGBA', (780, 90), (255, 255, 255, 220))
    message_draw = ImageDraw.Draw(message_box)
    message_draw.rectangle([(0, 0), (779, 89)], outline=(0, 0, 0), width=2)
    
    y_position = 10
    for line in lines:
        message_draw.text((20, y_position), line, fill=(0, 0, 0), font=small_font)
        y_position += 24
    
    frame.paste(message_box, (10, 400), message_box)
    
    return frame

def create_pokemon_shadow(pokemon_sprite: Image.Image) -> Image.Image:
    """
    Create an elliptical shadow for a Pokémon sprite (game-style)
    
    Args:
        pokemon_sprite: The Pokémon sprite image
        
    Returns:
        Shadow image with transparency
    """
    # Get dimensions
    width, height = pokemon_sprite.size
    
    # Create a new blank image for the shadow
    shadow = Image.new('RGBA', (width, int(height * 0.3)), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    
    # Calculate ellipse dimensions - use sprite width to determine shadow size
    sprite_width = width
    
    # Draw an elliptical shadow - make shadow slightly larger for larger sprites
    shadow_width = int(sprite_width * 0.9)  # Increased from 0.8 to 0.9
    shadow_height = int(shadow_width * 0.4)  # Shadow height relative to width
    
    # Center the ellipse
    x1 = (width - shadow_width) // 2
    y1 = (shadow.height - shadow_height) // 2
    x2 = x1 + shadow_width
    y2 = y1 + shadow_height
    
    # Draw the shadow ellipse
    shadow_draw.ellipse([(x1, y1), (x2, y2)], fill=(0, 0, 0, 80))
    
    # Apply a slight gaussian blur if PIL supports it
    try:
        from PIL import ImageFilter
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=1.5))
    except (ImportError, AttributeError):
        # If blur isn't available, that's okay
        pass
    
    return shadow

def generate_battle_animation(
    pokemon1_data: Dict[str, Any],
    pokemon2_data: Dict[str, Any],
    battle_result: Dict[str, Any],
    output_path: str = "battle.gif",
    use_shiny: bool = False
) -> str:
    """
    Generate a Pokémon battle animation GIF
    
    Args:
        pokemon1_data: Data for the first Pokémon
        pokemon2_data: Data for the second Pokémon
        battle_result: Battle result with winner and reasoning
        output_path: Path to save the resulting GIF
        use_shiny: Whether to use shiny sprites
        
    Returns:
        Path to the generated GIF
    """
    # Get sprites with appropriate variants
    # Randomly decide if we should use female sprites when available
    use_female1 = random.random() < 0.3  # 30% chance for female sprite if available
    use_female2 = random.random() < 0.3
    
    # Determine sprite variants
    sprite_variant1 = "default"
    if use_shiny and use_female1:
        sprite_variant1 = "shiny_female"
    elif use_shiny:
        sprite_variant1 = "shiny"
    elif use_female1:
        sprite_variant1 = "female"
        
    sprite_variant2 = "default"
    if use_shiny and use_female2:
        sprite_variant2 = "shiny_female"
    elif use_shiny:
        sprite_variant2 = "shiny"
    elif use_female2:
        sprite_variant2 = "female"
    
    # Get sprites with the selected variants - using back sprite for the first Pokémon
    pokemon1_sprite = get_pokemon_sprite(pokemon1_data["name"], sprite_variant1, is_first_pokemon=True)
    pokemon2_sprite = get_pokemon_sprite(pokemon2_data["name"], sprite_variant2, is_first_pokemon=False)
    
    # Determine winner and extract data
    winner_name = battle_result.get("winner", "").lower()
    reasoning = battle_result.get("reasoning", "Battle concluded!")
    
    # Determine type effectiveness and adjust battle accordingly
    type_effectiveness = get_type_effectiveness(pokemon1_data, pokemon2_data)
    
    # Create frames
    frames = []
    
    # Initial frame
    frames.append(create_battle_frame(
        pokemon1_sprite, pokemon2_sprite,
        pokemon1_data["name"], pokemon2_data["name"],
        1.0, 1.0,
        f"Battle begins! {pokemon1_data['name'].capitalize()} vs {pokemon2_data['name'].capitalize()}"
    ))
    
    # Simulate battle with more frames for smoother animation
    num_frames = random.randint(12, 15)  # Increased from 6-8 to 12-15 frames for smoother animation
    
    # Generate battle messages based on Pokémon types and stats
    messages = generate_battle_messages(pokemon1_data, pokemon2_data, type_effectiveness)
    
    p1_health = 1.0
    p2_health = 1.0
    
    # Determine final health based on winner
    p1_final_health = 0.2 if winner_name == pokemon1_data["name"].lower() else 0.0
    p2_final_health = 0.2 if winner_name == pokemon2_data["name"].lower() else 0.0
    
    # Generate smoother health decreases that reflect type effectiveness
    p1_decreases, p2_decreases = generate_health_decreases(
        num_frames, 
        p1_final_health, 
        p2_final_health, 
        type_effectiveness
    )
    
    # For each battle message, create multiple frames to make the text stay longer
    # This effectively slows down the battle animation
    battle_frames = []
    for i in range(num_frames):
        p1_health = max(0, 1.0 - p1_decreases[i])
        p2_health = max(0, 1.0 - p2_decreases[i])
        
        # Select appropriate message for this frame, ensuring no attack messages for fainted Pokémon
        message_index = i % len(messages)
        message = messages[message_index]
        
        # Skip attack messages for fainted Pokémon
        while ((p1_health <= 0 and message.startswith(pokemon1_data["name"].capitalize())) or
               (p2_health <= 0 and message.startswith(pokemon2_data["name"].capitalize()))) and len(messages) > 1:
            # Get a different message
            message_index = (message_index + 1) % len(messages)
            message = messages[message_index]
            
            # If we've cycled through all messages, use a generic one
            if message_index == i % len(messages):
                if p1_health <= 0:
                    message = f"{pokemon1_data['name'].capitalize()} has fainted!"
                    break
                elif p2_health <= 0:
                    message = f"{pokemon2_data['name'].capitalize()} has fainted!"
                    break
        
        # Create the frame
        frame = create_battle_frame(
            pokemon1_sprite, pokemon2_sprite,
            pokemon1_data["name"], pokemon2_data["name"],
            p1_health, p2_health,
            message
        )
        
        # Add the frame to our list
        battle_frames.append(frame)
        
        # For each message, create a duplicate frame to make it stay longer
        # This effectively doubles the time each message is shown
        battle_frames.append(frame)
    
    # Add all battle frames to the main frames list
    frames.extend(battle_frames)
    
    # Final frame with winner
    final_frame = create_battle_frame(
        pokemon1_sprite, pokemon2_sprite,
        pokemon1_data["name"], pokemon2_data["name"],
        p1_final_health, p2_final_health,
        f"{winner_name.capitalize()} wins the battle! {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}"
    )
    
    # Add the final frame multiple times to make it stay even longer
    frames.append(final_frame)
    frames.append(final_frame)  # Adding it twice more for emphasis
    frames.append(final_frame)
    
    # Save as GIF
    output_filename = f"battle_{int(time.time())}.gif"
    output_filepath = os.path.join(os.environ.get("TEMP_DIR", "/tmp"), output_filename)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    
    # Create a list of durations for each frame (in seconds)
    durations = [1000.0]  # First frame (intro)
    durations.extend([1000.0] * (len(frames) - 4))  # Battle frames
    durations.extend([1000.0, 1000.0, 1000.0])  # Final frames
    
    # Save GIF with appropriate durations
    imageio.mimsave(output_filepath, frames, duration=durations, loop=0)
    
    return output_filepath

def get_type_effectiveness(pokemon1_data: Dict[str, Any], pokemon2_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate type effectiveness between two Pokémon
    
    Args:
        pokemon1_data: Data for the first Pokémon
        pokemon2_data: Data for the second Pokémon
        
    Returns:
        Dictionary with effectiveness multipliers
    """
    # This is a simplified version - in a full implementation you would use the actual type chart
    type_chart = {
        # Format: attacking -> defending -> effectiveness
        "normal": {"rock": 0.5, "ghost": 0, "steel": 0.5},
        "fire": {"fire": 0.5, "water": 0.5, "grass": 2, "ice": 2, "bug": 2, "rock": 0.5, "dragon": 0.5, "steel": 2},
        "water": {"fire": 2, "water": 0.5, "grass": 0.5, "ground": 2, "rock": 2, "dragon": 0.5},
        "electric": {"water": 2, "electric": 0.5, "grass": 0.5, "ground": 0, "flying": 2, "dragon": 0.5},
        "grass": {"fire": 0.5, "water": 2, "grass": 0.5, "poison": 0.5, "ground": 2, "flying": 0.5, "bug": 0.5, "rock": 2, "dragon": 0.5, "steel": 0.5},
        "ice": {"fire": 0.5, "water": 0.5, "grass": 2, "ice": 0.5, "ground": 2, "flying": 2, "dragon": 2, "steel": 0.5},
        "fighting": {"normal": 2, "ice": 2, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2, "ghost": 0, "dark": 2, "steel": 2, "fairy": 0.5},
        "poison": {"grass": 2, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0, "fairy": 2},
        "ground": {"fire": 2, "electric": 2, "grass": 0.5, "poison": 2, "flying": 0, "bug": 0.5, "rock": 2, "steel": 2},
        "flying": {"electric": 0.5, "grass": 2, "fighting": 2, "bug": 2, "rock": 0.5, "steel": 0.5},
        "psychic": {"fighting": 2, "poison": 2, "psychic": 0.5, "dark": 0, "steel": 0.5},
        "bug": {"fire": 0.5, "grass": 2, "fighting": 0.5, "poison": 0.5, "flying": 0.5, "psychic": 2, "ghost": 0.5, "dark": 2, "steel": 0.5, "fairy": 0.5},
        "rock": {"fire": 2, "ice": 2, "fighting": 0.5, "ground": 0.5, "flying": 2, "bug": 2, "steel": 0.5},
        "ghost": {"normal": 0, "psychic": 2, "ghost": 2, "dark": 0.5},
        "dragon": {"dragon": 2, "steel": 0.5, "fairy": 0},
        "dark": {"fighting": 0.5, "psychic": 2, "ghost": 2, "dark": 0.5, "fairy": 0.5},
        "steel": {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2, "rock": 2, "steel": 0.5, "fairy": 2},
        "fairy": {"fighting": 2, "poison": 0.5, "bug": 0.5, "dragon": 2, "dark": 2, "steel": 0.5}
    }
    
    # Calculate base effectiveness
    p1_effectiveness = 1.0
    p2_effectiveness = 1.0
    
    # Get types
    p1_types = pokemon1_data.get("types", [])
    p2_types = pokemon2_data.get("types", [])
    
    # Calculate P1's effectiveness against P2
    for attack_type in p1_types:
        for defend_type in p2_types:
            if attack_type in type_chart and defend_type in type_chart.get(attack_type, {}):
                p1_effectiveness *= type_chart[attack_type][defend_type]
    
    # Calculate P2's effectiveness against P1
    for attack_type in p2_types:
        for defend_type in p1_types:
            if attack_type in type_chart and defend_type in type_chart.get(attack_type, {}):
                p2_effectiveness *= type_chart[attack_type][defend_type]
    
    return {
        "p1_against_p2": p1_effectiveness,
        "p2_against_p1": p2_effectiveness
    }

def generate_battle_messages(
    pokemon1_data: Dict[str, Any], 
    pokemon2_data: Dict[str, Any],
    type_effectiveness: Dict[str, float]
) -> List[str]:
    """
    Generate appropriate battle messages based on Pokémon types and stats
    
    Args:
        pokemon1_data: Data for the first Pokémon
        pokemon2_data: Data for the second Pokémon
        type_effectiveness: Type effectiveness data
        
    Returns:
        List of battle messages
    """
    p1_name = pokemon1_data["name"].capitalize()
    p2_name = pokemon2_data["name"].capitalize()
    
    # Get types for more specific messages
    p1_types = pokemon1_data.get("types", [])
    p2_types = pokemon2_data.get("types", [])
    
    # Get base stats for more specific messages
    p1_stats = pokemon1_data.get("base_stats", {})
    p2_stats = pokemon2_data.get("base_stats", {})
    
    messages = []
    
    # Basic attack messages
    messages.append(f"{p1_name} attacks {p2_name}!")
    messages.append(f"{p2_name} strikes back!")
    
    # More detailed type-based messages
    for p1_type in p1_types:
        if p1_type == "fire":
            messages.append(f"{p1_name} uses a powerful Fire-type move!")
            messages.append(f"{p1_name} unleashes a fiery attack!")
        elif p1_type == "water":
            messages.append(f"{p1_name} uses a Water-type attack!")
            messages.append(f"{p1_name} splashes {p2_name} with a Water attack!")
        elif p1_type == "electric":
            messages.append(f"{p1_name} unleashes an Electric attack!")
            messages.append(f"{p1_name} shocks {p2_name} with electricity!")
        elif p1_type == "grass":
            messages.append(f"{p1_name} uses a Grass-type move!")
            messages.append(f"{p1_name} attacks with plant power!")
        elif p1_type == "poison":
            messages.append(f"{p1_name} tries to poison {p2_name}!")
            messages.append(f"{p1_name} uses a Poison-type attack!")
        elif p1_type == "ground":
            messages.append(f"{p1_name} causes an earthquake!")
            messages.append(f"{p1_name} uses a Ground-type move!")
        elif p1_type == "flying":
            messages.append(f"{p1_name} attacks from the air!")
            messages.append(f"{p1_name} uses a Flying-type move!")
        elif p1_type == "psychic":
            messages.append(f"{p1_name} uses psychic powers!")
            messages.append(f"{p1_name} confuses {p2_name} with a Psychic attack!")
        elif p1_type == "bug":
            messages.append(f"{p1_name} uses a Bug-type move!")
            messages.append(f"{p1_name} swarms {p2_name}!")
        elif p1_type == "rock":
            messages.append(f"{p1_name} hurls rocks at {p2_name}!")
            messages.append(f"{p1_name} uses a Rock-type move!")
        elif p1_type == "ghost":
            messages.append(f"{p1_name} uses a spooky Ghost-type move!")
            messages.append(f"{p1_name} disappears and surprises {p2_name}!")
        elif p1_type == "ice":
            messages.append(f"{p1_name} uses a freezing Ice-type move!")
            messages.append(f"{p1_name} creates a blizzard!")
        elif p1_type == "dragon":
            messages.append(f"{p1_name} unleashes dragon fury!")
            messages.append(f"{p1_name} uses a mighty Dragon-type move!")
        elif p1_type == "dark":
            messages.append(f"{p1_name} uses a sneaky Dark-type move!")
            messages.append(f"{p1_name} attacks from the shadows!")
        elif p1_type == "steel":
            messages.append(f"{p1_name} uses a solid Steel-type move!")
            messages.append(f"{p1_name}'s body becomes metallic!")
        elif p1_type == "fairy":
            messages.append(f"{p1_name} uses Fairy magic!")
            messages.append(f"{p1_name} sparkles with Fairy-type energy!")
        else:
            messages.append(f"{p1_name} uses a {p1_type.capitalize()}-type move!")
    
    for p2_type in p2_types:
        if p2_type == "fire":
            messages.append(f"{p2_name} uses a powerful Fire-type move!")
            messages.append(f"{p2_name} unleashes a fiery attack!")
        elif p2_type == "water":
            messages.append(f"{p2_name} uses a Water-type attack!")
            messages.append(f"{p2_name} splashes {p1_name} with a Water attack!")
        elif p2_type == "electric":
            messages.append(f"{p2_name} unleashes an Electric attack!")
            messages.append(f"{p2_name} shocks {p1_name} with electricity!")
        elif p2_type == "grass":
            messages.append(f"{p2_name} uses a Grass-type move!")
            messages.append(f"{p2_name} attacks with plant power!")
        elif p2_type == "poison":
            messages.append(f"{p2_name} tries to poison {p1_name}!")
            messages.append(f"{p2_name} uses a Poison-type attack!")
        elif p2_type == "ground":
            messages.append(f"{p2_name} causes an earthquake!")
            messages.append(f"{p2_name} uses a Ground-type move!")
        elif p2_type == "flying":
            messages.append(f"{p2_name} attacks from the air!")
            messages.append(f"{p2_name} uses a Flying-type move!")
        elif p2_type == "psychic":
            messages.append(f"{p2_name} uses psychic powers!")
            messages.append(f"{p2_name} confuses {p1_name} with a Psychic attack!")
        elif p2_type == "bug":
            messages.append(f"{p2_name} uses a Bug-type move!")
            messages.append(f"{p2_name} swarms {p1_name}!")
        elif p2_type == "rock":
            messages.append(f"{p2_name} hurls rocks at {p1_name}!")
            messages.append(f"{p2_name} uses a Rock-type move!")
        elif p2_type == "ghost":
            messages.append(f"{p2_name} uses a spooky Ghost-type move!")
            messages.append(f"{p2_name} disappears and surprises {p1_name}!")
        elif p2_type == "ice":
            messages.append(f"{p2_name} uses a freezing Ice-type move!")
            messages.append(f"{p2_name} creates a blizzard!")
        elif p2_type == "dragon":
            messages.append(f"{p2_name} unleashes dragon fury!")
            messages.append(f"{p2_name} uses a mighty Dragon-type move!")
        elif p2_type == "dark":
            messages.append(f"{p2_name} uses a sneaky Dark-type move!")
            messages.append(f"{p2_name} attacks from the shadows!")
        elif p2_type == "steel":
            messages.append(f"{p2_name} uses a solid Steel-type move!")
            messages.append(f"{p2_name}'s body becomes metallic!")
        elif p2_type == "fairy":
            messages.append(f"{p2_name} uses Fairy magic!")
            messages.append(f"{p2_name} sparkles with Fairy-type energy!")
        else:
            messages.append(f"{p2_name} uses a {p2_type.capitalize()}-type move!")
    
    # Super effective messages
    if type_effectiveness["p1_against_p2"] > 1.0:
        messages.append(f"{p1_name}'s attack is super effective!")
        messages.append(f"It's super effective against {p2_name}!")
    if type_effectiveness["p2_against_p1"] > 1.0:
        messages.append(f"{p2_name}'s attack is super effective!")
        messages.append(f"It's super effective against {p1_name}!")
    
    # Not very effective messages
    if type_effectiveness["p1_against_p2"] < 1.0:
        messages.append(f"{p1_name}'s attack is not very effective...")
        messages.append(f"{p2_name} resists the attack!")
    if type_effectiveness["p2_against_p1"] < 1.0:
        messages.append(f"{p2_name}'s attack is not very effective...")
        messages.append(f"{p1_name} resists the attack!")
    
    # Stat-based messages
    if p1_stats.get("speed", 0) > p2_stats.get("speed", 0):
        messages.append(f"{p1_name} moves quickly with its superior speed!")
        messages.append(f"{p1_name} attacks first due to its speed!")
    else:
        messages.append(f"{p2_name} moves quickly with its superior speed!")
        messages.append(f"{p2_name} attacks first due to its speed!")
    
    if p1_stats.get("attack", 0) > p2_stats.get("attack", 0):
        messages.append(f"{p1_name} hits hard with its strong attack!")
        messages.append(f"{p1_name}'s powerful strike damages {p2_name}!")
    else:
        messages.append(f"{p2_name} hits hard with its strong attack!")
        messages.append(f"{p2_name}'s powerful strike damages {p1_name}!")
    
    if p1_stats.get("defense", 0) > p2_stats.get("defense", 0):
        messages.append(f"{p1_name} withstands the attack with its high defense!")
        messages.append(f"{p1_name} shows impressive defense!")
    else:
        messages.append(f"{p2_name} withstands the attack with its high defense!")
        messages.append(f"{p2_name} shows impressive defense!")
    
    # Add some generic messages
    messages.extend([
        f"Both Pokémon are battling hard!",
        f"{p1_name} dodges and prepares to strike!",
        f"{p2_name} is charging a powerful attack!",
        f"The battle intensifies as both Pokémon give it their all!",
        f"{p1_name} and {p2_name} circle each other cautiously.",
        f"{p1_name} looks determined to win!",
        f"{p2_name} refuses to back down!",
        f"The air crackles with energy as the battle continues!"
    ])
    
    # Shuffle the messages to get a random order
    random.shuffle(messages)
    
    return messages

def generate_health_decreases(
    num_frames: int, 
    p1_final_health: float, 
    p2_final_health: float,
    type_effectiveness: Dict[str, float]
) -> Tuple[List[float], List[float]]:
    """
    Generate health decrease patterns that reflect type effectiveness
    
    Args:
        num_frames: Number of battle frames
        p1_final_health: Final health for Pokémon 1
        p2_final_health: Final health for Pokémon 2
        type_effectiveness: Type effectiveness data
        
    Returns:
        Tuple of (p1_decreases, p2_decreases) lists
    """
    # Base decrease patterns
    p1_decreases = np.zeros(num_frames)
    p2_decreases = np.zeros(num_frames)
    
    # Adjust rate of health decrease based on type effectiveness
    p1_rate = min(2.0, max(0.5, type_effectiveness["p2_against_p1"]))
    p2_rate = min(2.0, max(0.5, type_effectiveness["p1_against_p2"]))
    
    # Generate some random points where damage occurs
    p1_damage_frames = sorted(random.sample(range(num_frames), min(4, num_frames)))
    p2_damage_frames = sorted(random.sample(range(num_frames), min(4, num_frames)))
    
    # Apply damage at those frames
    for frame in p1_damage_frames:
        p1_decreases[frame:] += (1.0 - p1_final_health) / len(p1_damage_frames) * p1_rate
    
    for frame in p2_damage_frames:
        p2_decreases[frame:] += (1.0 - p2_final_health) / len(p2_damage_frames) * p2_rate
    
    # Ensure we reach the final health exactly
    if p1_decreases[-1] > 0:
        p1_decreases = p1_decreases * ((1.0 - p1_final_health) / p1_decreases[-1])
    
    if p2_decreases[-1] > 0:
        p2_decreases = p2_decreases * ((1.0 - p2_final_health) / p2_decreases[-1])
    
    return p1_decreases, p2_decreases