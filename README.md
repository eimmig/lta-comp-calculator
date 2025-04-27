# LTA Fantasy Advisor

## Description
LTA Fantasy Advisor is a Python-based command-line tool that helps users make informed decisions for their fantasy league team selections. The tool analyzes player statistics, match data, and market prices to provide optimal team composition recommendations within a given budget.

## Features
- Player performance analysis across different roles
- Match data analysis for upcoming games
- Team composition optimization based on budget constraints
- Market price analysis and value assessment
- Statistical analysis of player performance
- Support for multiple player roles (top, jungle, mid, bottom, support)

## Project Structure
```
lta-fantasy-advisor/
├── src/
│   ├── api/               # API integration modules
│   │   ├── market_api.py  # Market data fetching
│   │   └── stats_api.py   # Player statistics
│   ├── cli/              # Command-line interface
│   │   └── advisor_cli.py # Main CLI implementation
│   ├── domain/           # Domain models and exceptions
│   │   ├── exceptions.py
│   │   └── models.py
│   ├── services/         # Business logic services
│   │   ├── match_analysis.py
│   │   ├── player_analysis.py
│   │   └── team_composition.py
│   └── utils/            # Utility functions
│       ├── calculators.py
│       └── formatters.py
└── tests/               # Test directory
```

## Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/lta-fantasy-advisor.git
cd lta-fantasy-advisor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage
Run the advisor using the provided batch file or directly with Python:

```bash
# Using batch file
run_advisor.bat

# Using Python directly
python run_advisor.py [options]
```

### Command Line Options
- `-k, --key`: Column index to sort role tables (default: 0)
- `-r, --reverse`: Sort column in reverse order
- `-v, --valorTotal`: Total available budget for team composition

## Features in Detail

### Player Analysis
- Statistical performance tracking
- Role-based evaluation
- Price trend analysis
- Match history analysis

### Team Composition
- Budget-based team optimization
- Role balance consideration
- Match-up analysis
- Value optimization

### Market Analysis
- Price tracking
- Value assessment
- Team average cost analysis
- Performance/cost ratio evaluation

## Development

### Dependencies
See `requirements.txt` for a full list of dependencies.

### Project Components
- **API Layer**: Handles data fetching from external sources
- **Service Layer**: Contains core business logic
- **Domain Layer**: Defines data models and business objects
- **CLI Layer**: Handles user interaction
- **Utils**: Common utilities and helper functions

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.