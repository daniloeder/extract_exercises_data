from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json, requests

def write_to_json(data, filename):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def extract_information(html_content):
    extracted_data = {}
    soup = BeautifulSoup(html_content, 'html.parser')
    title_tag = soup.find('h2') or soup.find('h3')
    title = title_tag.get_text(strip=True) if title_tag else None
    extracted_data['title'] = title.replace('How to do:', '').replace('How to do ', '').replace('How to do', '').replace('How to: ', '')
    description_tag = soup.find('p')
    description = description_tag.get_text(strip=True) if description_tag else None
    extracted_data['description'] = description
    how_to_do_tag = soup.find('h3', string='How to do:') or soup.find('h2', string=lambda text: text and 'How to do' in text)
    if how_to_do_tag:
        next_sibling = how_to_do_tag.find_next_sibling()
        how_to_do = []
        while next_sibling and next_sibling.name not in ['h3', 'h2']:
            if next_sibling.name == 'p' and next_sibling.get_text(strip=True) not in ['', 'Starting Position:', 'Execution:', 'Repetitions:']:
                how_to_do.append(next_sibling.get_text(strip=True))
            elif next_sibling.name in ['ol', 'ul']:
                for li in next_sibling.find_all('li', recursive=False):
                    how_to_do.append(li.get_text(strip=True))
            next_sibling = next_sibling.find_next_sibling()
    else:
        howtodo = [p.get_text(strip=True) for p in soup.find_all('h3', string='How to do:')]
        how_to_do = howtodo[0].find_next_siblings('p') if howtodo else None
    extracted_data['how_to_do'] = how_to_do
    comments_and_tips_tag = soup.find('h3', string='Comments and Tips:')
    if comments_and_tips_tag:
        comments_and_tips = comments_and_tips_tag.find_next('ol') or comments_and_tips_tag.find_next('ul') or comments_and_tips_tag.find_next('p')
        comments_and_tips = [item.get_text(strip=True) for item in comments_and_tips.find_all(['li', 'p'])]
    else:
        comments_and_tips = None
    extracted_data['comments_and_tips'] = comments_and_tips
    benefits_tag = soup.find('h3', string='Benefits')
    benefits = [li.get_text(strip=True) for li in benefits_tag.find_next('ul').find_all('li')] if benefits_tag else None
    extracted_data['benefits'] = benefits
    muscle_groups_tag = soup.find('div', class_='muscle_groups')
    muscle_groups = [li.find('span').get_text(strip=True) for li in muscle_groups_tag.find_all('li')] if muscle_groups_tag else None
    extracted_data['muscle_groups'] = muscle_groups
    equipment_tag = soup.find('div', class_='equipments')
    equipment = [li.find('span').get_text(strip=True) for li in equipment_tag.find_all('li')] if equipment_tag else None
    extracted_data['equipment'] = equipment
    # Extract the GIF image with class "aligncenter" and its alt
    gif_image_tag = soup.find('img', class_='aligncenter') or soup.find('img', class_='alignnone') or soup.find('div', class_='aligncenter').find('img')
    if gif_image_tag:
        gif_image_src = gif_image_tag['src'] if gif_image_tag else None
        gif_image_alt = gif_image_tag['alt'] if gif_image_tag else None
        extracted_data['gif_image'] = {'src': gif_image_src, 'alt': gif_image_alt}
    # Extract the muscle progress bar percentages
    muscle_progress_bar_tags = soup.find_all('div', class_='vc_progress_bar')
    muscle_progress_percentages = {}
    for tag in muscle_progress_bar_tags:
        small_labels = tag.find_all('small', class_='vc_label')
        vc_bars = tag.find_all('span', class_='vc_bar')
        for small_label, vc_bar in zip(small_labels, vc_bars):
            muscle_label = small_label.get_text(strip=True)
            percentage_value = vc_bar['data-percentage-value']
            muscle_progress_percentages[muscle_label] = percentage_value
    extracted_data['muscle_progress_percentages'] = muscle_progress_percentages
    # Extract the muscle activation image alt
    muscle_activation_image_tag = soup.find('img', class_='vc_single_image-img')
    if muscle_activation_image_tag:
        extracted_data['muscle_activation_image'] = {'src': muscle_activation_image_tag['src'], 'alt': muscle_activation_image_tag['alt'].replace('\xa0', '')}
    return extracted_data


def read_data_from_json(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file '{file_path}': {e}")
        return None

data = read_data_from_json('../exercises.json')

import os
from urllib.parse import urlparse
from django.conf import settings
from exercises.models import Exercise, MuscleGroup, ExerciseExecutionImage, MuscleActivationImage

# ['neck', 'trapezius', 'erector_spinae', 'abs', 'yoga', 'chest', 'shoulders', 'back-wing', 'hip', 'triceps', 'full_body', 'leg', 'calisthenic', 'cardio', 'stretch', 'biceps', 'forearm', 'hip_flexors', 'glutes', 'lower_back', 'middle_back', 'calf', 'calves']


muscle_groups_data = {'neck': 'Neck', 'trapezius': 'Trapezius', 'shoulders': 'Shoulders', 'chest': 'Chest', 'back': 'Back', 'erector_spinae': 'Erector Spinae', 'biceps': 'Biceps', 'triceps': 'Triceps', 'forearm': 'Forearm', 'abs': 'Abs', 'leg': 'Leg', 'calf': 'Calf', 'hip': 'Hip', 'cardio': 'Cardio', 'full_body': 'Full Body'}
for group_id, name in muscle_groups_data.items():
    MuscleGroup.objects.create(group_id=group_id, name=name)
    a = {}

for muscle_id, exercises in data.items():
    for exercise_id, exercise_info in exercises.items():
        # Extract the exercise information
        title = exercise_info.get('title', '')
        description = exercise_info.get('description', '')
        how_to_do = exercise_info.get('how_to_do', [])
        comments_and_tips = exercise_info.get('comments_and_tips', [])
        benefits = exercise_info.get('benefits', [])
        equipment = exercise_info.get('equipment', [])
        # Extract the muscle group
        muscle_group, _ = MuscleGroup.objects.get_or_create(group_id=muscle_id.lower().replace(' / ', '_').replace('_wing', '').replace('-', '_'))
        # Extract the exercise execution image
        execution_image_url = exercise_info.get('gif_image', {}).get('src', '')
        execution_image_name = os.path.basename(urlparse(execution_image_url).path)
        execution_image_path = os.path.join(settings.MEDIA_ROOT, 'exercises', 'execution', execution_image_name)
        # Extract the muscle activation image if it exists
        muscle_activation_image_url = exercise_info.get('muscle_activation_image', {}).get('src', '')
        muscle_activation_image_name = os.path.basename(urlparse(muscle_activation_image_url).path) if muscle_activation_image_url else None
        muscle_activation_image_path = os.path.join(settings.MEDIA_ROOT, 'exercises', 'muscle_activation', muscle_activation_image_name) if muscle_activation_image_name else None
        # Check if the exercise already exists
        existing_exercise = Exercise.objects.filter(title=title).first()
        if existing_exercise:
            existing_exercise.item_groups.add(muscle_group)
            exercise_execution_image = ExerciseExecutionImage.objects.create(
                exercise=existing_exercise,
                image_url=execution_image_path
            )
            existing_exercise.execution_image = exercise_execution_image
            if muscle_activation_image_path:
                muscle_activation_image = MuscleActivationImage.objects.create(
                    exercise=existing_exercise,
                    image_url=muscle_activation_image_path
                )
                existing_exercise.muscle_activation_image = muscle_activation_image
            existing_exercise.save()
        else:
            # If the exercise doesn't exist, create it and associate it with the muscle group
            new_exercise = Exercise.objects.create(
                item_id=exercise_id,
                title=title,
                description=description,
                how_to_do=how_to_do,
                comments_and_tips=comments_and_tips,
                benefits=benefits,
                equipment=equipment
            )
            new_exercise.item_groups.add(muscle_group)
            new_exercise.save()
            # Create ExerciseExecutionImage instance and link it to the exercise
            exercise_execution_image = ExerciseExecutionImage.objects.create(
                exercise=new_exercise,
                image_url=execution_image_path
            )
            new_exercise.execution_image = exercise_execution_image
            # Create MuscleActivationImage instance and link it to the exercise if muscle_activation_image exists
            if muscle_activation_image_path:
                muscle_activation_image = MuscleActivationImage.objects.create(
                    exercise=new_exercise,
                    image_url=muscle_activation_image_path
                )
                new_exercise.muscle_activation_image = muscle_activation_image
            new_exercise.save()


from exercises.models import FoodGroup, Food

food_groups = [
    'Breakfast',
    'Lunch',
    'Dinner',
    'Snack',
    'Pre-workout',
    'Post-workout',
    'Beverage'
]

for group_name in food_groups:
    food_group, created = FoodGroup.objects.get_or_create(group_id=group_name.lower().replace('-', '_'), name=group_name)
    if created:
        print(f'FoodGroup "{food_group.name}" created.')
    else:
        print(f'FoodGroup "{food_group.name}" already exists.')




foods = [
    ['Oatmeal', 'Breakfast', 150, 'Healthy breakfast option', ['Cook oats in water', 'Add toppings of choice'], ['Add fruits for extra flavor', 'Use honey as a sweetener'], ['Rich in fiber', 'Good source of energy']],
    ['Pancakes', 'Breakfast', 300, 'Fluffy pancakes with syrup', ['Mix batter ingredients', 'Cook on griddle'], ['Top with fresh berries', 'Drizzle maple syrup'], ['Comfort food', 'Great for brunch']],
    ['Tuna Salad', 'Lunch', 250, 'Refreshing tuna salad', ['Mix tuna with veggies', 'Dress with vinaigrette'], ['Add avocado for creaminess', 'Serve on a bed of greens'], ['Omega-3 from tuna', 'Light and satisfying']],
    ['Pasta Carbonara', 'Dinner', 400, 'Creamy pasta with bacon', ['Cook pasta al dente', 'Toss with egg and bacon'], ['Use pecorino cheese', 'Season with black pepper'], ['Indulgent meal', 'Rich and flavorful']],
    ['Smoothie Bowl', 'Snack', 200, 'Colorful and nutritious smoothie bowl', ['Blend fruits and yogurt', 'Top with granola and seeds'], ['Add coconut flakes for texture', 'Drizzle with honey for sweetness'], ['Vitamins and antioxidants', 'Refreshing snack']],
    ['Chicken Wrap', 'Lunch', 350, 'Savory chicken wrap', ['Grill chicken strips', 'Wrap in tortilla with veggies'], ['Spread hummus for extra flavor', 'Add lettuce and tomatoes'], ['Protein-packed meal', 'Portable and easy to eat']],
    ['Vegetable Stir-fry', 'Dinner', 280, 'Vegetarian stir-fry with tofu', ['Sauté veggies and tofu', 'Season with soy sauce and ginger'], ['Use sesame oil for flavor', 'Garnish with green onions'], ['Plant-based protein', 'Low-calorie option']],
    ['Fruit Salad', 'Snack', 150, 'Refreshing mix of fruits', ['Cut fruits into bite-sized pieces', 'Combine in a bowl'], ['Sprinkle with mint leaves', 'Squeeze fresh lemon juice'], ['Vitamins and fiber', 'Hydrating snack']],
    ['Turkey Sandwich', 'Lunch', 280, 'Classic turkey sandwich', ['Layer turkey and veggies on bread', 'Add condiments like mayo or mustard'], ['Toast bread for crunch', 'Pair with pickles or chips'], ['Lean protein from turkey', 'Satisfying and simple']],
    ['Rice Bowl', 'Dinner', 320, 'Versatile rice bowl', ['Cook rice', 'Top with protein and veggies'], ['Drizzle with soy sauce', 'Sprinkle with sesame seeds'], ['Customizable with toppings', 'Filling and hearty']],
    ['Fruit Smoothie', 'Snack', 120, 'Refreshing fruit smoothie', ['Blend fruits with yogurt or milk', 'Pour into a glass'], ['Add spinach for nutrients', 'Sweeten with honey or agave'], ['Antioxidants and vitamins', 'Quick and easy to make']],
    ['Egg Salad Sandwich', 'Lunch', 250, 'Creamy egg salad on bread', ['Boil and chop eggs', 'Mix with mayo and seasonings'], ['Add mustard for tang', 'Top with lettuce and tomato'], ['Protein from eggs', 'Great for picnics or lunches']],
    ['Trail Mix', 'Snack', 180, 'Nutty and sweet snack mix', None, ['Include a variety of nuts and dried fruits', 'Watch portion sizes for calorie control'], ['Energy from nuts', 'Portable and convenient']],
    ['Hummus and Veggie Sticks', 'Snack', 100, 'Creamy hummus with crunchy veggies', None, ['Try carrots, cucumbers, and bell peppers', 'Make your own hummus for freshness'], ['Fiber and vitamins from veggies', 'Protein and fiber from hummus']],
    ['Quinoa Salad', 'Lunch', 250, 'Nutritious quinoa salad', ['Cook quinoa and let cool', 'Mix with veggies and dressing'], ['Add fresh herbs for flavor', 'Top with feta cheese'], ['Complete protein from quinoa', 'Healthy and satisfying']],
    ['Apple Slices with Peanut Butter', 'Snack', 150, 'Sweet and savory snack combo', None, ['Sprinkle with chia seeds', 'Use almond butter for a twist'], ['Fiber and protein combo', 'Crunchy and creamy textures']],
    ['Cottage Cheese with Pineapple', 'Snack', 120, 'Creamy cottage cheese with sweet pineapple', None, ['Try with canned or fresh pineapple', 'Add a sprinkle of cinnamon for flavor'], ['Protein from cottage cheese', 'Vitamin C from pineapple']],
    ['Chia Seed Pudding', 'Snack', 180, 'Chia seeds soaked in milk or yogurt', None, ['Top with fresh fruit or nuts', 'Sweeten with maple syrup or agave'], ['Omega-3 fatty acids from chia seeds', 'Fiber and protein-rich']],
    ['Caprese Salad', 'Lunch', 200, 'Classic Italian salad with tomatoes and mozzarella', ['Slice tomatoes and mozzarella', 'Layer with basil leaves and drizzle with balsamic glaze'], ['Use ripe tomatoes for best flavor', 'Sprinkle with sea salt and black pepper'], ['Antioxidants from tomatoes', 'Calcium from mozzarella']],
    ['Almond Butter and Jelly Sandwich', 'Snack', 220, 'Nutty and sweet sandwich option', ['Spread almond butter and jelly on bread', 'Press together and cut into halves'], ['Use whole grain bread for added fiber', 'Try different nut butters for variety'], ['Protein from almond butter', 'Childhood favorite with a twist']],
    ['Cucumber Salad', 'Lunch', 120, 'Refreshing cucumber salad', ['Slice cucumbers and onions', 'Toss with vinegar and dill'], ['Chill in the fridge before serving', 'Garnish with feta cheese or olives'], ['Hydrating cucumbers', 'Healthy and nutritious']],
    ['Greek Yogurt', 'Snack', 150, 'Creamy and protein-rich yogurt', None, ['Top with fresh fruits or granola', 'Add a drizzle of honey for sweetness'], ['Probiotics for gut health', 'High in protein']],
    ['Scrambled Eggs', 'Breakfast', 180, 'Fluffy scrambled eggs', ['Whisk eggs and cook in a pan', 'Season with salt and pepper'], ['Add cheese or veggies for extra flavor', 'Serve with toast or avocado'], ['Protein-packed breakfast', 'Versatile and easy to make']],
    ['Grilled Chicken Salad', 'Lunch', 300, 'Grilled chicken over fresh greens', ['Grill or bake chicken breast', 'Toss with lettuce, veggies, and dressing'], ['Add avocado or nuts for extra nutrients', 'Drizzle with balsamic vinaigrette'], ['Lean protein from chicken', 'Nutrient-dense and filling']],
    ['Lentil Soup', 'Lunch', 250, 'Hearty and comforting lentil soup', ['Simmer lentils with veggies and broth', 'Season with herbs and spices'], ['Top with a dollop of yogurt', 'Serve with crusty bread'], ['Fiber and protein from lentils', 'Warm and satisfying']],
    ['Baked Salmon', 'Dinner', 350, 'Flaky and flavorful baked salmon', ['Season salmon fillets with herbs and lemon', 'Bake in the oven until cooked through'], ['Serve with roasted veggies', 'Drizzle with a lemon butter sauce'], ['Omega-3 fatty acids from salmon', 'Healthy and delicious']],
    ['Quinoa Bowl', 'Lunch', 280, 'Nutritious quinoa bowl with veggies', ['Cook quinoa and let cool', 'Top with roasted veggies and a protein source'], ['Drizzle with a vinaigrette or tahini sauce', 'Garnish with fresh herbs'], ['Complete protein from quinoa', 'Customizable and filling']],
    ['Vegetable Stir-fry', 'Dinner', 280, 'Vegetarian stir-fry with tofu', ['Sauté veggies and tofu', 'Season with soy sauce and ginger'], ['Use sesame oil for flavor', 'Garnish with green onions'], ['Plant-based protein', 'Low-calorie option']],
    ['Egg White Omelet', 'Breakfast', 150, 'Fluffy egg white omelet', ['Whisk egg whites and cook in a pan', 'Fill with veggies and cheese'], ['Top with salsa or avocado', 'Serve with a side of fruit'], ['High in protein, low in calories', 'Nutrient-dense breakfast']],
    ['Peanut Butter Toast', 'Snack', 200, 'Peanut butter on whole grain toast', None, ['Top with sliced bananas or berries', 'Drizzle with honey for extra sweetness'], ['Protein and fiber combo', 'Quick and satisfying snack']],
    ['Chicken Breast', 'Dinner', 250, 'Grilled or baked chicken breast', ['Season chicken with herbs and spices', 'Cook until juices run clear'], ['Serve with roasted veggies or a salad', 'Drizzle with a flavorful sauce'], ['Lean protein source', 'Versatile and easy to prepare']],
    ['Tuna Salad Sandwich', 'Lunch', 300, 'Tuna salad on whole grain bread', ['Mix tuna with mayo, veggies, and seasonings', 'Spread on bread and top with lettuce'], ['Add avocado or cheese for extra flavor', 'Serve with a side of fresh fruit'], ['Protein from tuna', 'Healthy and filling']],
    ['Grilled Steak', 'Dinner', 450, 'Juicy grilled steak', ['Season steak with salt and pepper', 'Grill to desired doneness'], ['Serve with roasted potatoes and veggies', 'Top with a pat of herb butter'], ['Protein-rich meal', 'Indulgent and flavorful']],
    ['Sweet Potato Fries', 'Snack', 200, 'Crispy baked sweet potato fries', ['Cut sweet potatoes into fry shapes', 'Toss with oil and bake until crispy'], ['Season with salt, pepper, and spices', 'Serve with a dipping sauce'], ['Vitamin A from sweet potatoes', 'Healthier alternative to regular fries']],
    ['Vegetable Medley', 'Snack', 100, 'Assorted roasted vegetables', ['Toss veggies with oil, salt, and pepper', 'Roast in the oven until tender'], ['Try different veggie combinations', 'Drizzle with balsamic glaze'], ['Nutrient-dense side dish', 'Versatile and flavorful']],
    ['Avocado Toast', 'Snack', 250, 'Avocado mashed on whole grain toast', None, ['Top with a fried egg or sliced tomatoes', 'Sprinkle with red pepper flakes or everything bagel seasoning'], ['Healthy fats from avocado', 'Satisfying and nutritious']],
    ['Berry Smoothie', 'Snack', 180, 'Refreshing berry smoothie', ['Blend berries with yogurt or milk', 'Add a handful of spinach or kale'], ['Sweeten with honey or a banana', 'Pour into a glass and enjoy'], ['Antioxidants from berries', 'Quick and easy to make']],
    ['Overnight Oats', 'Breakfast', 250, 'Creamy overnight oats', ['Mix oats with milk or yogurt and let soak overnight', 'Top with fresh fruits and nuts'], ['Add a drizzle of maple syrup or honey', 'Sprinkle with cinnamon or vanilla extract'], ['Fiber-rich breakfast', 'Convenient and customizable']],
    ['Chickpea Salad', 'Lunch', 220, 'Protein-packed chickpea salad', ['Mix chickpeas with veggies and a vinaigrette', 'Season with herbs and spices'], ['Add feta cheese or avocado for extra flavor', 'Serve on a bed of greens or in a wrap'], ['Plant-based protein', 'Nutrient-dense and filling']],
    ['Baked Sweet Potato', 'Snack', 150, 'Baked sweet potato', ['Prick sweet potato with a fork and bake until tender', 'Top with desired toppings'], ['Try butter, cinnamon, or a dollop of Greek yogurt', 'Sprinkle with chopped nuts or seeds'], ['Vitamin A and fiber', 'Versatile and satisfying side']],
    ['Grilled Vegetables', 'Snack', 100, 'Assorted grilled vegetables', ['Toss veggies with oil and seasonings', 'Grill until tender and slightly charred'], ['Try zucchini, bell peppers, onions, and mushrooms', 'Drizzle with a balsamic glaze'], ['Nutrient-dense side dish', 'Flavorful and easy to prepare']],
    ['Tofu Stir-fry', 'Dinner', 300, 'Vegetarian tofu stir-fry', ['Sauté tofu and veggies in a wok', 'Season with soy sauce, ginger, and garlic'], ['Add a protein source like edamame or cashews', 'Serve over steamed rice or quinoa'], ['Plant-based protein', 'Flavorful and filling']],
    ['Egg Whites', 'Breakfast', 100, 'Fluffy egg whites', ['Whisk egg whites and cook in a pan', 'Fill with veggies and cheese'], ['Top with salsa or avocado', 'Serve with a side of fruit'], ['High in protein, low in calories', 'Nutrient-dense breakfast']],
    ['Cucumber Water', 'Beverage', 10, 'Refreshing cucumber-infused water', None, ['Slice cucumbers and add to a pitcher of water', 'Let infuse for a few hours before drinking'], ['Hydrating and refreshing', 'Low-calorie and flavorful']],
    ['Herbal Tea', 'Beverage', 0, 'Soothing herbal tea', None, ['Try different herbal blends like chamomile or peppermint', 'Add a squeeze of lemon or a drizzle of honey'], ['Caffeine-free and calming', 'Potential health benefits']],
    ['Coconut Water', 'Beverage', 60, 'Refreshing coconut water', None, ['Drink straight from the bottle or over ice', 'Add a squeeze of lime for extra flavor'], ['Hydrating and electrolyte-rich', 'Natural and low in calories']],
    ['Fruit Infused Water', 'Beverage', 20, 'Flavorful fruit-infused water', None, ['Add sliced fruits like lemons, limes, or berries to water', 'Let infuse for a few hours before drinking'], ['Hydrating and refreshing', 'Natural sweetness from fruits']],
    ['Vegetable Broth', 'Beverage', 30, 'Savory vegetable broth', ['Simmer vegetables and herbs in water', 'Strain and season with salt and pepper'], ['Use as a base for soups or sauces', 'Sip on its own for a warm and comforting drink'], ['Low-calorie and nutrient-rich', 'Flavorful and versatile']],
    ['Yogurt', 'Snack', 150, 'Creamy and protein-rich yogurt', None, ['Top with fresh fruits or granola', 'Add a drizzle of honey for sweetness'], ['Probiotics for gut health', 'High in protein']],
    ['Grilled Chicken', 'Dinner', 250, 'Grilled or baked chicken breast', ['Season chicken with herbs and spices', 'Cook until juices run clear'], ['Serve with roasted veggies or a salad', 'Drizzle with a flavorful sauce'], ['Lean protein source', 'Versatile and easy to prepare']],
    ['Mixed Greens', 'Snack', 30, 'Fresh mixed greens salad', None, ['Toss with a vinaigrette or dressing of choice', 'Add toppings like nuts, seeds, or cheese'], ['Nutrient-dense and low-calorie', 'Versatile base for salads']],
    ['Quinoa', 'Snack', 200, 'Fluffy and nutty quinoa', ['Cook quinoa according to package instructions', 'Season with herbs and spices'], ['Toss with roasted veggies or a protein source', 'Drizzle with a vinaigrette or sauce'], ['Complete plant-based protein', 'Fiber-rich and versatile']],
    ['Baked Fish', 'Dinner', 300, 'Flaky and flavorful baked fish', ['Season fish fillets with herbs and lemon', 'Bake in the oven until cooked through'], ['Serve with roasted veggies or a salad', 'Drizzle with a lemon butter sauce'], ['Lean protein source', 'Healthy and delicious']],
    ['Roasted Vegetables', 'Snack', 100, 'Assorted roasted vegetables', ['Toss veggies with oil, salt, and pepper', 'Roast in the oven until tender'], ['Try different veggie combinations', 'Drizzle with balsamic glaze'], ['Nutrient-dense side dish', 'Versatile and flavorful']],
    ['Whole Grain Pasta', 'Snack', 200, 'Whole grain pasta', ['Cook pasta according to package instructions', 'Toss with a sauce or dressing of choice'], ['Add roasted veggies or a protein source', 'Sprinkle with grated cheese or fresh herbs'], ['Fiber-rich and satisfying', 'Versatile base for meals']],
    ['Chicken Salad', 'Lunch', 300, 'Creamy chicken salad', ['Mix shredded chicken with mayo, veggies, and seasonings', 'Serve on a bed of greens or in a sandwich'], ['Add nuts or dried fruits for extra crunch and flavor', 'Sprinkle with fresh herbs'], ['Protein-packed and satisfying', 'Versatile and flavorful']],
    ['Grilled Salmon', 'Dinner', 350, 'Grilled or baked salmon', ['Season salmon fillets with herbs and lemon', 'Grill or bake until cooked through'], ['Serve with roasted veggies or a salad', 'Drizzle with a lemon butter sauce'], ['Omega-3 fatty acids', 'Healthy and delicious']],
    ['Quinoa Pilaf', 'Snack', 250, 'Flavorful quinoa pilaf', ['Cook quinoa with broth and seasonings', 'Add sautéed veggies and herbs'], ['Toss with a squeeze of lemon juice', 'Garnish with toasted nuts or seeds'], ['Protein-rich and fiber-filled', 'Versatile and flavorful side dish']],
    ['Roasted Brussels Sprouts', 'Snack', 150, 'Crispy roasted Brussels sprouts', ['Toss Brussels sprouts with oil, salt, and pepper', 'Roast in the oven until crispy and caramelized'], ['Drizzle with balsamic glaze', 'Add a squeeze of lemon juice for extra flavor'], ['Nutrient-dense side dish', 'Versatile and flavorful']],
    ['Veggie Omelet', 'Breakfast', 200, 'Veggie-packed omelet', ['Whisk eggs and cook in a pan', 'Fill with sautéed veggies and cheese'], ['Top with salsa or avocado', 'Serve with a side of whole grain toast'], ['Protein-rich breakfast', 'Nutrient-dense and filling']],
    ['Chia Pudding', 'Snack', 180, 'Chia seeds soaked in milk or yogurt', None, ['Top with fresh fruit or nuts', 'Sweeten with maple syrup or agave'], ['Omega-3 fatty acids from chia seeds', 'Fiber and protein-rich']],
    ['Water', 'Beverage', 0, 'Plain water', None, ['Drink throughout the day to stay hydrated', 'Add lemon or fruit slices for extra flavor'], ['Essential for overall health', 'Calorie-free and refreshing']],
 ]


for food_name, group_name, calories, description, how_to_make, comments_and_tips, benefits in foods:
    food_group = FoodGroup.objects.get(name=group_name)
    try:
        food, created = Food.objects.get_or_create(
            item_id=food_name.lower().replace(' ', '_').replace('-', '_'),
            title=food_name,
            calories=calories,
            description=description,
            how_to_make=how_to_make,
            comments_and_tips=comments_and_tips,
            benefits=benefits
        )
        food.item_groups.add(food_group)
    except:
        print(f'Error with {food_name}')


access_token='EAAAl2IAG1D9JwGV7vt53Z6PGSFQTmDeRRkuEYAGfcjniP8AsNYyquNIcysMdF00'
idempotency_key="a79a71fd-54c1-4d3d-b789-308087747070"
test_card_number = "4111 1111 1111 1111"
test_exp_date = "12/2025"
test_postal_code = "90210"

from square.http.auth.o_auth_2 import BearerAuthCredentials
from square.client import Client
import os

client = Client(
    bearer_auth_credentials=BearerAuthCredentials(
        access_token=access_token
    ),
    environment='sandbox'
)

result = client.payments.create_payment(
    body = {
        "source_id": "sqn:" + test_card_number,
        "idempotency_key": idempotency_key,
        "amount_money": {
        "amount": 100,
        "currency": "USD"
        },
        "billing_address": {
        "postal_code": test_postal_code
        }
    }
)

result = client.payments.create_payment(
  body = {
    "source_id": "cnon:card-nonce-ok",
    "idempotency_key": idempotency_key,
    "amount_money": {
      "amount": 100,
      "currency": "USD"
    }
  }
)
from users.models import CustomUser
from payments.models import Statement

for user in CustomUser.objects.all().order_by('id'):
    statement = Statement.objects.create(
        user=user
    )
    user.statement = statement
    user.save()

import requests
from common.models import USDPrice
#quotes = requests.get('https://open.er-api.com/v6/latest/USD').json()

quotes = {'result': 'success', 'provider': 'https://www.exchangerate-api.com', 'documentation': 'https://www.exchangerate-api.com/docs/free', 'terms_of_use': 'https://www.exchangerate-api.com/terms', 'time_last_update_unix': 1717718551, 'time_last_update_utc': 'Fri, 07 Jun 2024 00:02:31 +0000', 'time_next_update_unix': 1717806061, 'time_next_update_utc': 'Sat, 08 Jun 2024 00:21:01 +0000', 'time_eol_unix': 0, 'base_code': 'USD', 'rates': {'USD': 1, 'AED': 3.6725, 'AFN': 70.530653, 'ALL': 92.246099, 'AMD': 387.988774, 'ANG': 1.79, 'AOA': 862.236397, 'ARS': 864.75, 'AUD': 1.501286, 'AWG': 1.79, 'AZN': 1.700011, 'BAM': 1.797043, 'BBD': 2, 'BDT': 117.464899, 'BGN': 1.797375, 'BHD': 0.376, 'BIF': 2863.084048, 'BMD': 1, 'BND': 1.346495, 'BOB': 6.923734, 'BRL': 5.297629, 'BSD': 1, 'BTN': 83.499668, 'BWP': 13.735225, 'BYN': 3.265222, 'BZD': 2, 'CAD': 1.367419, 'CDF': 2794.55849, 'CHF': 0.890685, 'CLP': 909.596139, 'CNY': 7.249076, 'COP': 3930.104585, 'CRC': 529.262079, 'CUP': 24, 'CVE': 101.312958, 'CZK': 22.604262, 'DJF': 177.721, 'DKK': 6.852424, 'DOP': 59.249357, 'DZD': 134.443626, 'EGP': 47.538988, 'ERN': 15, 'ETB': 57.543189, 'EUR': 0.918815, 'FJD': 2.256665, 'FKP': 0.782196, 'FOK': 6.852466, 'GBP': 0.782198, 'GEL': 2.815034, 'GGP': 0.782196, 'GHS': 14.986719, 'GIP': 0.782196, 'GMD': 66.713735, 'GNF': 8576.530008, 'GTQ': 7.767826, 'GYD': 209.223531, 'HKD': 7.810237, 'HNL': 24.706023, 'HRK': 6.922799, 'HTG': 132.569921, 'HUF': 358.450938, 'IDR': 16276.266211, 'ILS': 3.728291, 'IMP': 0.782196, 'INR': 83.4997, 'IQD': 1308.553929, 'IRR': 42081.948915, 'ISK': 137.594212, 'JEP': 0.782196, 'JMD': 155.49487, 'JOD': 0.709, 'JPY': 155.806769, 'KES': 130.419838, 'KGS': 87.392741, 'KHR': 4091.952242, 'KID': 1.501283, 'KMF': 452.026555, 'KRW': 1366.167742, 'KWD': 0.306416, 'KYD': 0.833333, 'KZT': 447.47411, 'LAK': 21655.197511, 'LBP': 89500, 'LKR': 302.533842, 'LRD': 193.946922, 'LSL': 18.967522, 'LYD': 4.833092, 'MAD': 9.909869, 'MDL': 17.650361, 'MGA': 4480.192948, 'MKD': 56.666817, 'MMK': 2099.002061, 'MNT': 3409.227029, 'MOP': 8.044544, 'MRU': 39.404295, 'MUR': 46.09984, 'MVR': 15.436676, 'MWK': 1739.875435, 'MXN': 17.737245, 'MYR': 4.694705, 'MZN': 63.760974, 'NAD': 18.967522, 'NGN': 1480.736557, 'NIO': 36.814381, 'NOK': 10.56248, 'NPR': 133.599469, 'NZD': 1.614237, 'OMR': 0.384497, 'PAB': 1, 'PEN': 3.749249, 'PGK': 3.858728, 'PHP': 58.668157, 'PKR': 278.550388, 'PLN': 3.941945, 'PYG': 7508.687778, 'QAR': 3.64, 'RON': 4.575615, 'RSD': 107.601256, 'RUB': 89.019063, 'RWF': 1310.415326, 'SAR': 3.75, 'SBD': 8.330167, 'SCR': 13.454586, 'SDG': 511.591335, 'SEK': 10.390308, 'SGD': 1.346496, 'SHP': 0.782196, 'SLE': 22.442048, 'SLL': 22442.047967, 'SOS': 571.259206, 'SRD': 31.95895, 'SSP': 1711.226684, 'STN': 22.510928, 'SYP': 12910.620929, 'SZL': 18.967522, 'THB': 36.448674, 'TJS': 10.795044, 'TMT': 3.499636, 'TND': 3.103679, 'TOP': 2.330879, 'TRY': 32.29887, 'TTD': 6.749906, 'TVD': 1.501283, 'TWD': 32.281261, 'TZS': 2609.400632, 'UAH': 40.156747, 'UGX': 3793.184176, 'UYU': 38.85616, 'UZS': 12696.561725, 'VES': 36.4882, 'VND': 25390.920872, 'VUV': 119.209218, 'WST': 2.721989, 'XAF': 602.702073, 'XCD': 2.7, 'XDR': 0.754279, 'XOF': 602.702073, 'XPF': 109.643839, 'YER': 250.32977, 'ZAR': 18.967564, 'ZMW': 26.36792, 'ZWL': 13.4356}}

for currency, rate in quotes['rates'].items():
    USDPrice.objects.update_or_create(
        currency=currency,
        value=rate
    )
