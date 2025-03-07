import json
import time
import random
import os
from datetime import datetime
from faker import Faker
from kafka import KafkaProducer


fake = Faker()


CATEGORIES = ["Hotels", "Restaurants", "Attractions", "Tours", "Transportation", "Beaches", "Museums", "Adventure", "Cruises", "Resorts"]


POSITIVE_WORDS = ["amazing", "beautiful", "relaxing", "stunning", "delicious", "comfortable", "friendly", "luxurious", "peaceful", "unforgettable"]
NEGATIVE_WORDS = ["disappointing", "dirty", "expensive", "crowded", "rude", "noisy", "uncomfortable", "boring", "overpriced", "terrible"]

def create_producer():
    """Create and return a Kafka producer instance."""
    
    bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:29092')
    print(f"Connecting to Kafka at: {bootstrap_servers}")
    
    
    for attempt in range(1, 6):
        try:
            producer = KafkaProducer(
                bootstrap_servers=[bootstrap_servers],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                
                retries=5,
                acks='all'
            )
            print("Successfully connected to Kafka")
            return producer
        except Exception as e:
            print(f"Connection attempt {attempt} failed: {e}")
            if attempt < 5:
                sleep_time = 2 ** attempt  
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print("All connection attempts failed. Exiting.")
                raise

def generate_review():
    """Generate a fake tourism review with embedded sentiment."""
    
    sentiment_bias = random.choices(['positive', 'negative', 'neutral'], weights=[0.5, 0.3, 0.2])[0]
    
    
    username = fake.user_name()
    
    
    business_types = {
        "Hotels": ["Hotel", "Resort", "Inn", "Suites", "Lodge"],
        "Restaurants": ["Restaurant", "Café", "Bistro", "Diner", "Eatery"],
        "Attractions": ["Park", "Garden", "Monument", "Castle", "Palace"],
        "Tours": ["Tour", "Excursion", "Safari", "Walk", "Expedition"],
        "Transportation": ["Rental", "Shuttle", "Ferry", "Train", "Bus"],
        "Beaches": ["Beach", "Cove", "Bay", "Shore", "Coast"],
        "Museums": ["Museum", "Gallery", "Exhibition", "Collection", "Heritage Center"],
        "Adventure": ["Hiking", "Diving", "Rafting", "Climbing", "Zipline"],
        "Cruises": ["Cruise", "Boat Tour", "Yacht Charter", "Sailing", "River Cruise"],
        "Resorts": ["Resort", "Spa", "Retreat", "Villa", "Bungalow"]
    }
    
    
    category = random.choice(CATEGORIES)
    business_type = random.choice(business_types.get(category, ["Place"]))
    
    
    location = fake.city()
    
    
    if random.random() < 0.5:
        
        adjective = fake.word().capitalize()
        product = f"The {adjective} {business_type} of {location}"
    else:
        
        adjective = fake.word().capitalize()
        product = f"{location} {adjective} {business_type}"
    
    rating = 0
    
    
    if sentiment_bias == 'positive':
        rating = random.randint(4, 5)
        positive_count = random.randint(1, 3)
        
        
        templates = [
            f"Our stay at {product} was {{positive_word}}. {fake.paragraph()}",
            f"I visited {product} during my trip to {location} and it was {{positive_word}}. {fake.paragraph()}",
            f"The experience at {product} was {{positive_word}}. {fake.paragraph()}",
            f"If you're visiting {location}, {product} is {{positive_word}}. {fake.paragraph()}"
        ]
        
        review_text = random.choice(templates).format(positive_word=random.choice(POSITIVE_WORDS))
        
        
        for _ in range(positive_count - 1):
            positive_word = random.choice(POSITIVE_WORDS)
            random_word = fake.word()
            review_text = review_text.replace(random_word, positive_word, 1)
    
    elif sentiment_bias == 'negative':
        rating = random.randint(1, 2)
        negative_count = random.randint(1, 3)
        
        
        templates = [
            f"Our experience at {product} was {{negative_word}}. {fake.paragraph()}",
            f"I was disappointed with {product} during my visit to {location}. It was {{negative_word}}. {fake.paragraph()}",
            f"The service at {product} was {{negative_word}}. {fake.paragraph()}",
            f"I would not recommend {product} to anyone visiting {location}. It was {{negative_word}}. {fake.paragraph()}"
        ]
        
        review_text = random.choice(templates).format(negative_word=random.choice(NEGATIVE_WORDS))
        
        
        for _ in range(negative_count - 1):
            negative_word = random.choice(NEGATIVE_WORDS)
            random_word = fake.word()
            review_text = review_text.replace(random_word, negative_word, 1)
    
    else:  
        rating = 3
        
        
        templates = [
            f"{product} was average. {fake.paragraph()}",
            f"My stay at {product} in {location} was neither great nor terrible. {fake.paragraph()}",
            f"{product} met our basic expectations. {fake.paragraph()}",
            f"The {category.lower()} experience at {product} was acceptable but nothing special. {fake.paragraph()}"
        ]
        
        review_text = random.choice(templates)
    
    
    timestamp = datetime.now().isoformat()
    review = {
        "review_id": fake.uuid4(),
        "username": username,
        "product": product,
        "category": category,
        "location": location,
        "rating": rating,
        "review_text": review_text,
        "sentiment_bias": sentiment_bias,  
        "timestamp": timestamp
    }
    
    return review

def run_producer(topic_name=os.environ.get('KAFKA_TOPIC', 'tourism_reviews') , frequency=2, max_messages=None):
    """
    Run the Kafka producer to generate and send fake reviews.
    
    Args:
        topic_name: Kafka topic to send messages to
        frequency: Messages per second
        max_messages: Optional limit to number of messages (None for infinite)
    """
    producer = create_producer()
    delay = 1.0 / frequency
    count = 0
    
    try:
        print(f"Starting to send messages to topic '{topic_name}' at {frequency} messages per second...")
        
        while max_messages is None or count < max_messages:
            
            review = generate_review()
            producer.send(topic_name, value=review)
            
            count += 1
            if count % 10 == 0:
                print(f"Sent {count} messages")
            
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print("\nStopping producer...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        producer.flush()
        producer.close()
        print(f"Producer stopped. Total messages sent: {count}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Kafka producer for fake product reviews')
    parser.add_argument('--topic', type=str, default='tourism_reviews', help='Kafka topic name')
    parser.add_argument('--frequency', type=float, default=0.033, help='Messages per second (0.033 = once every 30 seconds)')
    parser.add_argument('--max', type=int, default=None, help='Maximum number of messages to send')
    
    args = parser.parse_args()
    
    run_producer(topic_name=args.topic, frequency=args.frequency, max_messages=args.max)