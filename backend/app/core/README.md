# Checklists Folder Structure

## How to Add Checklists

1. Create a folder for each year (e.g., `2024`, `2025`)
2. Add CSV files inside year folders
3. Name CSV files after the set name (e.g., `Topps-Chrome.csv`, `Bowman.csv`)
4. Click "Rescan Folder" button in the app to import

## Folder Structure Example

```
checklists/
├── 2024/
│   ├── Topps-Chrome.csv
│   ├── Bowman.csv
│   └── Heritage.csv
├── 2025/
│   ├── Topps-Series-1.csv
│   └── Bowman-Chrome.csv
└── README.md (this file)
```

## CSV Format

Your CSV files should have the following columns (in order):

1. **Variety** - Card variety/type (Base, Refractor, Auto, etc.)
2. **Card Number** - Card number in the set
3. **Player/Athlete** - Player name
4. **Team** - Team name
5. **Rookie** - "Yes" or "No" (optional)
6. **Parallel** - Parallel variation name (optional)
7. **Unique Variety** - Additional variety info (optional)

### Example CSV Content

```csv
Variety,Card Number,Player/Athlete,Team,Rookie,Parallel,Unique Variety
Base,1,Mike Trout,Angels,No,,
Refractor,1,Mike Trout,Angels,No,Blue /150,
Auto,2,Shohei Ohtani,Angels,No,,
Base,3,Ronald Acuna Jr.,Braves,No,,
```

## Auto-Import

- The app will automatically scan this folder on startup
- CSV files are only imported once (duplicates are skipped)
- Click "Rescan Folder" to import newly added files
- Already imported files are ignored on rescan

## Tips

- Use descriptive file names (they become set names in the app)
- Keep CSVs organized by year in separate folders
- Make sure CSV files are UTF-8 encoded
- Include headers in your CSV files (they will be skipped)
