# Vonex Telecom - Python Scraper for Internet Points of Interconnection (POI)

## The Need:
Prior to the implementation of this scraper, the Iseek Cacti service had limitations in providing the necessary details required by Vonex's Network Operations Center (NOC) technicians to identify potential problems within the Vonex network. Information about the POI locations, Connectivity Virtual Circuit (CVC), bandwidth, and related data was restricted, causing delays in resolving network issues. Moreover, the absence of any alerting mechanism led to NOC technicians becoming aware of issues only when customers reported slow or disrupted internet services. Vonex recognized the importance of collecting data to develop models for investigating service irregularities and thus initiated the development of the Python Scraper.

## Functionality and Implementation:
The Python Scraper interacts with the Iseek Cacti service through HTTP POST requests to download CSV files containing bandwidth data for the past 12 hours, along with the titles of each POI. The `requests` library in Python is employed to facilitate this data retrieval process.

The titles of the POIs from the CSV files often lacked standardized formats, making it difficult to derive meaningful information from them. To address this issue, the scraper utilizes regular expressions (regex) to extract and create identifiable fields from the POI titles. These fields provide valuable insights about the POI locations, CVC details, bandwidth specifications, and more.

The scraper leverages a well-maintained XLSX file as a reference to fill in and enhance the collected data with additional useful information that can be obtained from other sources. This additional data might include geographical information, service providers, and historical performance metrics for comparison and analysis.

Originally, the data was stored in an MSSQL database, but it was later migrated to a Postgresql database for improved performance and scalability. The migration process ensured that data integrity was maintained during the transition, and it resulted in faster data retrieval and more efficient querying capabilities.

To ensure ease of deployment on different servers and operating systems, the Python Scraper is containerized using Docker. This allows the service to be deployed effortlessly on any Linux-based or Windows server with minimal setup and configuration time. The Docker image includes all the dependencies required for the scraper, making it highly portable and consistent across different environments.

The use of an Object-Relational Mapping (ORM) library during the development of the scraper enables seamless communication with the chosen database, irrespective of its specific type. This flexibility allows the scraper to be used with various database systems without major modifications, facilitating easy integration with existing infrastructure.

## Backup and Maintenance:
In addition to the scraper, backup scripts were created to ensure the continuity of the service even after the developer's departure from the company. Regular backups are scheduled to safeguard the collected data, configurations, and scripts. This ensures that the data collection and alerting mechanisms can be maintained and updated by the company's personnel with minimal disruptions.

## Display and Alerting:
Grafana, a powerful data visualization and monitoring platform, is employed to display the collected data and create alerting dashboards. The deep understanding of SQL by the developer allows them to craft informative and visually appealing dashboards in Grafana, providing an intuitive interface for NOC technicians to monitor the network health.

The scraper is integrated with an SMTP setup to send email alerts to Vonex's NOC technicians in real-time whenever there is an issue with any of the POIs. The alerting mechanism is based on predefined thresholds for POI bandwidth, inbound and outbound traffic, and any other relevant metrics. This ensures prompt attention to any disruptions or irregularities, minimizing customer impact and enhancing network reliability.

## Conclusion:
In conclusion, the Python Scraper created for Vonex Telecom proves to be a valuable asset for collecting critical data about Internet POIs. Its versatility, containerization, and integration with Grafana for visualization and alerting empower the NOC technicians to proactively identify and address network issues, leading to improved customer experiences and network performance. The scraper's ability to extract and standardize data from POI titles, along with its flexibility in database management, enables Vonex Telecom to make data-driven decisions and ensure the smooth functioning of their network infrastructure.
