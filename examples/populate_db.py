#!/usr/bin/env python3
"""
Vector DB Population Script

This script populates the vector database with test data across three topics:
1. Anime - with metadata like release_date, anime_name, genre, studio
2. Apple Products - with metadata like product_type, release_date, price_range
3. Programming Languages - with metadata like paradigm, year_created, difficulty_level

Creates three libraries with different indexing strategies:
- Linear Index
- IVF (Inverted File) Index  
- NSW (Navigable Small World) Index
"""

import asyncio
import httpx
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import json
import sys
import os
import time

# Add the app directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.embedding import CohereEmbedding

# Configuration
BASE_URL = "http://localhost:8000/v1"
# Set your Cohere API keys here or in environment variables
COHERE_API_KEYS = [
    "pa6sRhnVAedMVClPAwoCvC1MjHKEwjtcGSTjWRMd",
    "rQsWxQJOK89Gp87QHo6qnGtPiWerGJOxvdg59o5f"
]

class VectorDBPopulator:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.current_key_index = 0
        self.embedder = None
        self._init_embedder()
        
        # Store created library IDs for reference
        self.library_ids = {}
        
    def _init_embedder(self):
        """Initialize embedder with current API key"""
        os.environ["COHERE_API_KEY"] = COHERE_API_KEYS[self.current_key_index]
        self.embedder = CohereEmbedding()
        
    def _switch_api_key(self):
        """Switch to next API key if available"""
        if self.current_key_index < len(COHERE_API_KEYS) - 1:
            self.current_key_index += 1
            print(f"Switching to API key {self.current_key_index + 1}")
            self._init_embedder()
            return True
        return False
        
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    def get_test_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns structured test data for three topics with rich metadata.
        Multiple chunks about the same items for better testing.
        """
        return {
            "anime": [
                # Death Note chunks (3 chunks)
                {
                    "text": "Death Note is a psychological thriller anime about Light Yagami, a brilliant student who discovers a supernatural notebook.",
                    "metadata": {
                        "anime_name": "Death Note",
                        "release_date": "2006-10-04",
                        "genre": "Psychological Thriller",
                        "studio": "Madhouse",
                        "rating": 9.0,
                        "episodes": 37,
                        "status": "completed",
                        "chunk_type": "overview"
                    }
                },
                {
                    "text": "The Death Note grants its user the power to kill anyone by writing their name in the notebook while picturing their face.",
                    "metadata": {
                        "anime_name": "Death Note",
                        "release_date": "2006-10-04",
                        "genre": "Psychological Thriller",
                        "studio": "Madhouse",
                        "rating": 9.0,
                        "episodes": 37,
                        "status": "completed",
                        "chunk_type": "plot_mechanism"
                    }
                },
                {
                    "text": "Light Yagami uses the Death Note to eliminate criminals, believing he can create a perfect world, while L tries to catch him.",
                    "metadata": {
                        "anime_name": "Death Note",
                        "release_date": "2006-10-04",
                        "genre": "Psychological Thriller",
                        "studio": "Madhouse",
                        "rating": 9.0,
                        "episodes": 37,
                        "status": "completed",
                        "chunk_type": "character_conflict"
                    }
                },
                # Attack on Titan chunks (2 chunks)
                {
                    "text": "Attack on Titan depicts humanity's struggle for survival against giant humanoid creatures called Titans behind massive walls.",
                    "metadata": {
                        "anime_name": "Attack on Titan",
                        "release_date": "2013-04-07",
                        "genre": "Dark Fantasy",
                        "studio": "Studio Pierrot",
                        "rating": 9.1,
                        "episodes": 87,
                        "status": "completed",
                        "chunk_type": "world_setting"
                    }
                },
                {
                    "text": "Eren Yeager joins the Survey Corps to fight Titans after witnessing his mother's death during the fall of Wall Maria.",
                    "metadata": {
                        "anime_name": "Attack on Titan",
                        "release_date": "2013-04-07",
                        "genre": "Dark Fantasy",
                        "studio": "Studio Pierrot",
                        "rating": 9.1,
                        "episodes": 87,
                        "status": "completed",
                        "chunk_type": "protagonist_motivation"
                    }
                },
                # Demon Slayer chunks (2 chunks)
                {
                    "text": "Demon Slayer follows Tanjiro Kamado who becomes a demon slayer to find a cure for his sister Nezuko who turned into a demon.",
                    "metadata": {
                        "anime_name": "Demon Slayer",
                        "release_date": "2019-04-06",
                        "genre": "Supernatural",
                        "studio": "Ufotable",
                        "rating": 8.7,
                        "episodes": 44,
                        "status": "ongoing",
                        "chunk_type": "main_plot"
                    }
                },
                {
                    "text": "The Demon Slayer Corps uses special breathing techniques and Nichirin swords to fight demons that prey on humans.",
                    "metadata": {
                        "anime_name": "Demon Slayer",
                        "release_date": "2019-04-06",
                        "genre": "Supernatural",
                        "studio": "Ufotable",
                        "rating": 8.7,
                        "episodes": 44,
                        "status": "ongoing",
                        "chunk_type": "combat_system"
                    }
                },
                # One Piece chunks (3 chunks)
                {
                    "text": "One Piece follows Monkey D. Luffy's quest to become the Pirate King and find the legendary treasure called One Piece.",
                    "metadata": {
                        "anime_name": "One Piece",
                        "release_date": "1999-10-20",
                        "genre": "Adventure",
                        "studio": "Toei Animation",
                        "rating": 9.2,
                        "episodes": 1000,
                        "status": "ongoing",
                        "chunk_type": "main_quest"
                    }
                },
                {
                    "text": "Luffy has rubber powers from eating the Gomu Gomu no Mi Devil Fruit and assembles a diverse crew called the Straw Hat Pirates.",
                    "metadata": {
                        "anime_name": "One Piece",
                        "release_date": "1999-10-20",
                        "genre": "Adventure",
                        "studio": "Toei Animation",
                        "rating": 9.2,
                        "episodes": 1000,
                        "status": "ongoing",
                        "chunk_type": "protagonist_abilities"
                    }
                },
                {
                    "text": "The Grand Line is a dangerous sea route where pirates search for treasure while facing the World Government and other pirates.",
                    "metadata": {
                        "anime_name": "One Piece",
                        "release_date": "1999-10-20",
                        "genre": "Adventure",
                        "studio": "Toei Animation",
                        "rating": 9.2,
                        "episodes": 1000,
                        "status": "ongoing",
                        "chunk_type": "world_geography"
                    }
                }
            ],
            "apple": [
                # iPhone chunks (4 chunks)
                {
                    "text": "iPhone 15 Pro features a titanium design with the powerful A17 Pro chip for enhanced performance and efficiency.",
                    "metadata": {
                        "product_name": "iPhone 15 Pro",
                        "product_type": "smartphone",
                        "release_date": "2023-09-22",
                        "price_range": "premium",
                        "chip": "A17 Pro",
                        "material": "titanium",
                        "chunk_type": "design_performance"
                    }
                },
                {
                    "text": "The iPhone 15 Pro camera system includes a 48MP main camera, ultra-wide, and telephoto lenses with advanced computational photography.",
                    "metadata": {
                        "product_name": "iPhone 15 Pro",
                        "product_type": "smartphone",
                        "release_date": "2023-09-22",
                        "price_range": "premium",
                        "chip": "A17 Pro",
                        "material": "titanium",
                        "chunk_type": "camera_features"
                    }
                },
                {
                    "text": "iPhone 15 Pro supports USB-C connectivity and offers storage options from 128GB to 1TB with ProRAW and ProRes capabilities.",
                    "metadata": {
                        "product_name": "iPhone 15 Pro",
                        "product_type": "smartphone",
                        "release_date": "2023-09-22",
                        "price_range": "premium",
                        "chip": "A17 Pro",
                        "material": "titanium",
                        "chunk_type": "connectivity_storage"
                    }
                },
                {
                    "text": "The iPhone 15 Pro Action Button replaces the mute switch and can be customized for various functions and shortcuts.",
                    "metadata": {
                        "product_name": "iPhone 15 Pro",
                        "product_type": "smartphone",
                        "release_date": "2023-09-22",
                        "price_range": "premium",
                        "chip": "A17 Pro",
                        "material": "titanium",
                        "chunk_type": "user_interface"
                    }
                },
                # MacBook Air chunks (3 chunks)
                {
                    "text": "MacBook Air M2 delivers exceptional performance with the Apple M2 chip in an incredibly thin and lightweight design.",
                    "metadata": {
                        "product_name": "MacBook Air M2",
                        "product_type": "laptop",
                        "release_date": "2022-07-15",
                        "price_range": "mid-range",
                        "chip": "M2",
                        "form_factor": "ultrabook",
                        "chunk_type": "performance_design"
                    }
                },
                {
                    "text": "The MacBook Air M2 features a 13.6-inch Liquid Retina display with 500 nits brightness and P3 wide color gamut.",
                    "metadata": {
                        "product_name": "MacBook Air M2",
                        "product_type": "laptop",
                        "release_date": "2022-07-15",
                        "price_range": "mid-range",
                        "chip": "M2",
                        "form_factor": "ultrabook",
                        "chunk_type": "display_specs"
                    }
                },
                {
                    "text": "MacBook Air M2 offers up to 18 hours of battery life and comes in Midnight, Starlight, Space Gray, and Silver colors.",
                    "metadata": {
                        "product_name": "MacBook Air M2",
                        "product_type": "laptop",
                        "release_date": "2022-07-15",
                        "price_range": "mid-range",
                        "chip": "M2",
                        "form_factor": "ultrabook",
                        "chunk_type": "battery_options"
                    }
                },
                # AirPods chunks (3 chunks)
                {
                    "text": "AirPods Pro 2nd generation feature the H2 chip for enhanced Active Noise Cancellation and superior audio quality.",
                    "metadata": {
                        "product_name": "AirPods Pro 2nd Gen",
                        "product_type": "earbuds",
                        "release_date": "2022-09-23",
                        "price_range": "premium",
                        "chip": "H2",
                        "form_factor": "wireless earbuds",
                        "chunk_type": "audio_technology"
                    }
                },
                {
                    "text": "The AirPods Pro case supports MagSafe charging and includes a built-in speaker for Find My location tracking.",
                    "metadata": {
                        "product_name": "AirPods Pro 2nd Gen",
                        "product_type": "earbuds",
                        "release_date": "2022-09-23",
                        "price_range": "premium",
                        "chip": "H2",
                        "form_factor": "wireless earbuds",
                        "chunk_type": "charging_features"
                    }
                },
                {
                    "text": "AirPods Pro offer Spatial Audio with dynamic head tracking and up to 6 hours of listening time with ANC enabled.",
                    "metadata": {
                        "product_name": "AirPods Pro 2nd Gen",
                        "product_type": "earbuds",
                        "release_date": "2022-09-23",
                        "price_range": "premium",
                        "chip": "H2",
                        "form_factor": "wireless earbuds",
                        "chunk_type": "spatial_audio_battery"
                    }
                }
            ],
            "ai": [
                # ChatGPT/OpenAI chunks (3 chunks)
                {
                    "text": "ChatGPT is a conversational AI model developed by OpenAI based on the GPT (Generative Pre-trained Transformer) architecture.",
                    "metadata": {
                        "ai_name": "ChatGPT",
                        "company": "OpenAI",
                        "release_date": "2022-11-30",
                        "model_type": "Large Language Model",
                        "architecture": "Transformer",
                        "use_cases": ["conversation", "writing", "coding"],
                        "chunk_type": "overview"
                    }
                },
                {
                    "text": "ChatGPT uses reinforcement learning from human feedback (RLHF) to improve its responses and align with human preferences.",
                    "metadata": {
                        "ai_name": "ChatGPT",
                        "company": "OpenAI",
                        "release_date": "2022-11-30",
                        "model_type": "Large Language Model",
                        "architecture": "Transformer",
                        "use_cases": ["conversation", "writing", "coding"],
                        "chunk_type": "training_method"
                    }
                },
                {
                    "text": "ChatGPT can assist with various tasks including creative writing, code generation, problem-solving, and educational support.",
                    "metadata": {
                        "ai_name": "ChatGPT",
                        "company": "OpenAI",
                        "release_date": "2022-11-30",
                        "model_type": "Large Language Model",
                        "architecture": "Transformer",
                        "use_cases": ["conversation", "writing", "coding"],
                        "chunk_type": "capabilities"
                    }
                },
                # Claude chunks (3 chunks)
                {
                    "text": "Claude is an AI assistant created by Anthropic, designed to be helpful, harmless, and honest in its interactions.",
                    "metadata": {
                        "ai_name": "Claude",
                        "company": "Anthropic",
                        "release_date": "2022-03-01",
                        "model_type": "Large Language Model",
                        "architecture": "Constitutional AI",
                        "use_cases": ["analysis", "writing", "research"],
                        "chunk_type": "overview"
                    }
                },
                {
                    "text": "Claude uses Constitutional AI training methods to reduce harmful outputs and improve alignment with human values.",
                    "metadata": {
                        "ai_name": "Claude",
                        "company": "Anthropic",
                        "release_date": "2022-03-01",
                        "model_type": "Large Language Model",
                        "architecture": "Constitutional AI",
                        "use_cases": ["analysis", "writing", "research"],
                        "chunk_type": "safety_approach"
                    }
                },
                {
                    "text": "Claude excels at complex reasoning, analysis, and maintaining context over long conversations with nuanced understanding.",
                    "metadata": {
                        "ai_name": "Claude",
                        "company": "Anthropic",
                        "release_date": "2022-03-01",
                        "model_type": "Large Language Model",
                        "architecture": "Constitutional AI",
                        "use_cases": ["analysis", "writing", "research"],
                        "chunk_type": "strengths"
                    }
                },
                # DALL-E chunks (2 chunks)
                {
                    "text": "DALL-E is an AI image generation model by OpenAI that creates images from textual descriptions using diffusion techniques.",
                    "metadata": {
                        "ai_name": "DALL-E",
                        "company": "OpenAI",
                        "release_date": "2021-01-05",
                        "model_type": "Image Generation",
                        "architecture": "Diffusion Model",
                        "use_cases": ["art creation", "design", "visualization"],
                        "chunk_type": "technology_overview"
                    }
                },
                {
                    "text": "DALL-E 3 features improved prompt following, higher image quality, and better understanding of complex scene descriptions.",
                    "metadata": {
                        "ai_name": "DALL-E",
                        "company": "OpenAI",
                        "release_date": "2021-01-05",
                        "model_type": "Image Generation",
                        "architecture": "Diffusion Model",
                        "use_cases": ["art creation", "design", "visualization"],
                        "chunk_type": "latest_improvements"
                    }
                },
                # GitHub Copilot chunks (2 chunks)
                {
                    "text": "GitHub Copilot is an AI programming assistant developed by GitHub and OpenAI that suggests code completions in real-time.",
                    "metadata": {
                        "ai_name": "GitHub Copilot",
                        "company": "GitHub",
                        "release_date": "2021-06-29",
                        "model_type": "Code Generation",
                        "architecture": "Codex",
                        "use_cases": ["code completion", "programming", "development"],
                        "chunk_type": "functionality"
                    }
                },
                {
                    "text": "Copilot is trained on billions of lines of public code and can generate functions, classes, and entire programs from comments.",
                    "metadata": {
                        "ai_name": "GitHub Copilot",
                        "company": "GitHub",
                        "release_date": "2021-06-29",
                        "model_type": "Code Generation",
                        "architecture": "Codex",
                        "use_cases": ["code completion", "programming", "development"],
                        "chunk_type": "training_capabilities"
                    }
                }
            ]
        }

    async def create_library(self, name: str, index_type: str, metadata: Dict[str, Any] = None, index_params: Dict[str, Any] = None) -> str:
        """Create a library and return its ID"""
        payload = {
            "name": name,
            "index_type": index_type,
            "metadata": metadata or {},
        }
        
        if index_params:
            payload["index_params"] = index_params
        
        print(f"Creating library: {name} with index type: {index_type}")
        
        response = await self.client.post(
            f"{self.base_url}/libraries/",
            json=payload
        )
        
        if response.status_code != 201:
            print(f"Failed to create library {name}: {response.status_code} - {response.text}")
            raise Exception(f"Failed to create library: {response.text}")
        
        library_data = response.json()
        library_id = library_data["id"]
        self.library_ids[name] = library_id
        print(f"✓ Created library {name} with ID: {library_id}")
        return library_id

    async def create_chunk(self, library_id: str, text: str, metadata: Dict[str, Any]) -> str:
        """Create a chunk in a library and return its ID"""
        
        # Generate embedding for the text with retry logic
        print(f"Generating embedding for: {text[:50]}...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                embedding = self.embedder.embed(text, input_type="search_document", dimension=1024)
                break
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "rate" in error_msg:
                    if attempt < max_retries - 1:
                        if self._switch_api_key():
                            print(f"Rate limited, switched API key, retrying...")
                            continue
                        else:
                            print(f"Rate limited, waiting 60 seconds...")
                            await asyncio.sleep(60)
                            continue
                    else:
                        print(f"All API keys exhausted or rate limited")
                        raise
                else:
                    print(f"Failed to generate embedding: {e}")
                    raise
        
        # Add small delay to avoid hitting rate limits
        await asyncio.sleep(1.5)
        
        payload = {
            "text": text,
            "metadata": metadata,
            "document_metadata": {}  # Will create a new document
        }
        
        response = await self.client.post(
            f"{self.base_url}/libraries/{library_id}/chunks/",
            json=payload
        )
        
        if response.status_code != 201:
            print(f"Failed to create chunk: {response.status_code} - {response.text}")
            raise Exception(f"Failed to create chunk: {response.text}")
        
        chunk_data = response.json()
        print(f"✓ Created chunk: {text[:30]}...")
        return chunk_data["id"]

    async def build_index(self, library_id: str, library_name: str):
        """Build index for a library"""
        print(f"Building index for library: {library_name}")
        
        response = await self.client.post(
            f"{self.base_url}/libraries/{library_id}/index"
        )
        
        if response.status_code != 200:
            print(f"Failed to build index for {library_name}: {response.status_code} - {response.text}")
            raise Exception(f"Failed to build index: {response.text}")
        
        print(f"✓ Built index for library: {library_name}")

    async def populate_library(self, library_name: str, library_id: str, topic_data: List[Dict[str, Any]]):
        """Populate a library with chunks from topic data"""
        print(f"\nPopulating library '{library_name}' with {len(topic_data)} chunks...")
        
        for i, chunk_data in enumerate(topic_data, 1):
            print(f"  Adding chunk {i}/{len(topic_data)}")
            await self.create_chunk(
                library_id=library_id,
                text=chunk_data["text"],
                metadata=chunk_data["metadata"]
            )
            
        print(f"✓ Completed populating library '{library_name}'")

    async def run_population(self):
        """Main method to populate the database"""
        print("🚀 Starting Vector DB Population...")
        print("=" * 60)
        
        try:
            # Get test data
            test_data = self.get_test_data()
            
            # Define libraries with SAME DATA but different index types for performance comparison
            # Using combined dataset from all three topics for comprehensive testing
            combined_topic_data = []
            for topic_name, topic_chunks in test_data.items():
                combined_topic_data.extend(topic_chunks)
            
            libraries_config = [
                {
                    "name": "Mixed Collection (Linear Index)",
                    "index_type": "linear",
                    "topic": "combined",
                    "data": combined_topic_data,
                    "metadata": {
                        "description": "Mixed anime, Apple, and AI data with linear search index",
                        "topics": ["anime", "apple", "ai"],
                        "index_strategy": "linear",
                        "total_chunks": len(combined_topic_data)
                    }
                },
                {
                    "name": "Mixed Collection (IVF Index)",
                    "index_type": "ivf", 
                    "topic": "combined",
                    "data": combined_topic_data,
                    "metadata": {
                        "description": "Mixed anime, Apple, and AI data with IVF clustering index",
                        "topics": ["anime", "apple", "ai"],
                        "index_strategy": "ivf",
                        "total_chunks": len(combined_topic_data)
                    },
                    "index_params": {
                        "n_clusters": 6,  # 6 clusters for better distribution across topics
                        "n_probes": 3
                    }
                },
                {
                    "name": "Mixed Collection (NSW Index)",
                    "index_type": "nsw",
                    "topic": "combined",
                    "data": combined_topic_data,
                    "metadata": {
                        "description": "Mixed anime, Apple, and AI data with NSW graph index",
                        "topics": ["anime", "apple", "ai"],
                        "index_strategy": "nsw",
                        "total_chunks": len(combined_topic_data)
                    },
                    "index_params": {
                        "max_connections": 8,
                        "ef_construction": 16
                    }
                }
            ]
            
            # Create libraries and populate them
            for lib_config in libraries_config:
                print(f"\n📚 Processing {lib_config['name']}")
                print("-" * 50)
                
                # Create library
                library_id = await self.create_library(
                    name=lib_config["name"],
                    index_type=lib_config["index_type"],
                    metadata=lib_config["metadata"],
                    index_params=lib_config.get("index_params")
                )
                
                # Populate with chunks (use combined data for all libraries)
                if lib_config["topic"] == "combined":
                    topic_data = lib_config["data"]
                else:
                    topic_data = test_data[lib_config["topic"]]
                await self.populate_library(lib_config["name"], library_id, topic_data)
                
                # Build index
                await self.build_index(library_id, lib_config["name"])
            
            print("\n" + "=" * 60)
            print("🎉 Successfully populated Vector DB!")
            print("\nCreated Libraries:")
            for name, lib_id in self.library_ids.items():
                print(f"  • {name}: {lib_id}")
            
            print(f"\nTotal chunks created: {sum(len(data) for data in test_data.values())}")
            
            # Print sample search queries for performance testing
            print("\n🔍 Performance Comparison Queries:")
            print("(Test the same queries across all three index types)")
            
            print("\n🎌 Anime Queries:")
            print("  • 'psychological thriller anime' (should find Death Note chunks)")
            print("  • 'giant creatures titans' (should find Attack on Titan chunks)")
            print("  • 'demon slayer sword fighting' (should find Demon Slayer chunks)")
            print("  • 'pirate adventure treasure' (should find One Piece chunks)")
            
            print("\n🍎 Apple Product Queries:")
            print("  • 'titanium smartphone camera' (should find iPhone 15 Pro chunks)")
            print("  • 'M2 chip laptop display' (should find MacBook Air chunks)")
            print("  • 'wireless earbuds noise cancellation' (should find AirPods chunks)")
            
            print("\n🤖 AI Technology Queries:")
            print("  • 'conversational AI chatbot' (should find ChatGPT chunks)")
            print("  • 'Constitutional AI safety' (should find Claude chunks)")
            print("  • 'image generation art' (should find DALL-E chunks)")
            print("  • 'code completion programming' (should find GitHub Copilot chunks)")
            
            print("\n📊 Performance Testing Tips:")
            print("  • Test search speed across Linear vs IVF vs NSW")
            print("  • Compare result quality and ranking")
            print("  • Try k=1, k=5, k=10 for different result counts")
            print("  • Use metadata filters to test combined filtering + search")
            
            print("\n🔧 Metadata Filtering Examples:")
            print("  • Filter by release_date > '2022-01-01'")
            print("  • Filter by product_type = 'smartphone'")
            print("  • Filter by company = 'OpenAI'")
            print("  • Filter by chunk_type = 'overview'")
            
        except Exception as e:
            print(f"❌ Error during population: {e}")
            raise

async def main():
    """Main entry point"""
    populator = VectorDBPopulator()
    
    try:
        # Check if the API is running
        response = await populator.client.get(f"{BASE_URL.replace('/v1', '')}/health")
        if response.status_code != 200:
            print("❌ Vector DB API is not running!")
            print("Please start the API with: uvicorn app.main:app --reload")
            return
        
        print("✓ Vector DB API is running")
        
        # Run the population
        await populator.run_population()
        
    except httpx.ConnectError:
        print("❌ Cannot connect to Vector DB API!")
        print("Please ensure the API is running on http://localhost:8000")
        print("Start it with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        await populator.close()

if __name__ == "__main__":
    asyncio.run(main())
