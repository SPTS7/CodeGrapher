import re

class ReportGenerator:
    """A simple class to generate reports."""

    def __init__(self, title):
        """Initializes the report generator."""
        self.title = title
        self.content = []

    def add_line(self, line):
        """Adds a line of text to the report content."""
        self.content.append(line)

    def generate(self):
        """Generates the final report string."""
        print(f"--- {self.title} ---")
        for line in self.content:
            print(line)
        print("--- End of Report ---")


def normalize_string(s):
    """Converts a string to lowercase and removes non-alphanumeric characters."""
    s = s.lower()
    return re.sub(r'[^a-z0-9\s]', '', s)


def clean_data(raw_data):
    """Cleans a list of raw data strings by normalizing them."""
    print("Cleaning data...")
    cleaned = [normalize_string(item) for item in raw_data]
    return cleaned


def read_data(source):
    """Simulates reading raw data from a source."""
    print(f"Reading data from {source}...")
    return ["User 1: Hello World!", "User 2: Test Data #123", "User 3: ANOTHER-EXAMPLE"]


def write_report(data):
    """Writes the processed data into a report."""
    print("Writing report...")
    report = ReportGenerator("Analysis Report")
    for item in data:
        report.add_line(f"Processed item: {item}")
    report.generate()


def process_data(source_file):
    """Main data processing pipeline."""
    print("Starting data processing pipeline...")
    raw_data = read_data(source_file)
    processed_data = clean_data(raw_data)
    write_report(processed_data)
    print("Pipeline finished.")


def main():
    """Main entry point for the script."""
    print("Application started.")
    process_data("dummy_source.txt")
    print("Application finished.")


if __name__ == "__main__":
    main()