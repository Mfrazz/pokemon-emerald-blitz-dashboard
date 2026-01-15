import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///PokemonDraftData.db")

tables = pd.read_sql(
    "SELECT name FROM sqlite_master WHERE type='table';",
    engine
)

print(tables)

print('all_draft_csv_with_website')

df = pd.read_sql("SELECT * FROM all_draft_csv_with_website", engine)
print(df.head())

print('pre_website_w_2for1s')

df = pd.read_sql("SELECT * FROM pre_website_w_2for1s", engine)
print(df.head())

print('pre_website_2for1_only!')

df = pd.read_sql("SELECT * FROM 'pre_website_2for1_only!'", engine)
print(df.head())

print('draft_event')

df = pd.read_sql("SELECT * FROM draft_event", engine)
print(df.head())

print('draft_players')

df = pd.read_sql("SELECT * FROM draft_players", engine)
print(df.head())

print('draft_pokemon')

df = pd.read_sql("SELECT * FROM draft_pokemon", engine)
print(df.head())

print('draft_event_V2')

df = pd.read_sql("SELECT * FROM draft_event_V2", engine)
print(df.head())

print('draft_players_V2')

df = pd.read_sql("SELECT * FROM draft_players_V2", engine)
print(df.head())

print('draft_pokemon_V2')

df = pd.read_sql("SELECT * FROM draft_pokemon_V2", engine)
print(df.head())







