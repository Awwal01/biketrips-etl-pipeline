# biketrips-etl-pipeline
This repo contains an ETL pipeline that processes and analyzes bike trips data using AWS services. The pipeline uses Airflow to orchestrate the tasks, S3 to store the data, Glue to catalog and transform the data, EMR to run Spark jobs, Redshift to load and query the data, IAM to control access, and CloudFormation to provision resources.

This contain a sample of cloud ETL orchestration
## Table of Content
- Use Case
- Architecture Diagram
- How to Setup
- Data Flow
- Dag Diagram
- Infrastructure as Code
- How to Run It
- Clean Up
- How to Contribute
- References
- Licensing

## Use Case
The project simulates an end-to-end batch data processing workflow, using prebuilt operators for business use cases.
The workflow reduces the time for businesses to market their data product being event-driven and makes it easy to iterate over big data processes without the need to create custom solutions [Dish | Apache Airflow](https://airflow.apache.org/use-cases/dish/). The project contains documentation, source code as well and infrastructure as code. 

## Architecture Diagram

![Untitled Diagram (ETL MWAA workshop)3 drawio](https://github.com/Awwal01/biketrips-etl-pipeline/assets/53828785/486e7a44-417d-4506-aa0a-c3bff2f93302)

## How to SetUp
Prerequisite
- AWS Account
- IAM User and Role Setup
- Glue, EMR jobs
- Optional - Redshift (Serverless or Cluster) 
- S3 Bucket

### Installation steps 
#### Docker Compose Installation.
You can use this script /airflow/docker-compose-installation-script.sh to install docker and docker composer on your cloud9 environment.
```mkdir airflow && cd airflow && bash docker-compose-installation-script.sh```. 
Docker composes comes with docker desktop if using a Windows device, see this link ([docker/compose: Define and run multi-container applications with Docker (github.com)](https://github.com/docker/compose)) reference to docker compose installation. 
#### Airflow Installation
Non-relevant services to our project in original airflow docker-compose.yaml file were commented out like Celery. Also, the environment variables in .env files were passed to docker-compose using env_file
You can install airflow services using the scipt in /airflow/airflow-installation.sh
run 
```cd /airflow && bash airflow-installation.sh```.
see this link for more details on airflow installation on docker [airflow official docker installation link]([Running Airflow in Docker — Airflow Documentation (apache.org)](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)) and this video too  [(15) Airflow Tutorial for Beginners - Full Course in 2 Hours 2022 - YouTube](https://www.youtube.com/watch?v=K9AnJ9_ZAXE). 

### Cloud9 SetUP
You can follow this workshop [guide]([Amazon MWAA for Analytics Workshop (workshops.aws)](https://catalog.workshops.aws/amazon-mwaa-for-analytics/en-US/workshop/start-the-workshop/self-paced/deploy-resources)) to set up cloud9, or you can work with local machine. Changed the instance type to t3a.medium to satisfy most airflow setup requirements for cloud9 environment. On the Ec2 console page select the Cloud9 instance stop it, click `Actions` dropdown, and choose `Instance Settings` > `Change Instance Type` and select `t3a.medium` or high instance type.

## Data Flow
The raw data is loaded into s3. 
It is crawled using a Glue crawler to create a data catalog
A glue job is run to make some transformations on the data like columns renaming, and the transformed data is loaded into an s3 bucket
An EMR job is run to make aggregates on the transformed data creating new features. After processing, the data is loaded into another s3 bucket
*#optional* The data can be queried by Redshift using the Redshift spectrum or copied to a Redshift cluster using the copy operation. It can also be visualized in tools like Grafana Cloud after creating IAM role which Grafana can use to access the data
Link to source of data set - 

## DAG Diagram

![Pasted image 20231203101106](https://github.com/Awwal01/biketrips-etl-pipeline/assets/53828785/fd02c399-72e2-4dda-8051-23c57e665015)

![image](https://github.com/Awwal01/biketrips-etl-pipeline/assets/53828785/227965a2-59c5-4e93-ae76-31a86b04712c)

## Infrastructure As Code
The project leverages CloudFormation as an Infrastructure as its code tool.
You can download the template from the CloudFormation folder and upload it to your AWS CloudFormation Console page. Or you can launch the template programmatically using the AWS CLI.

### Stack Resources
- IAM Role for Glue, EMR and Redshift
- S3 Bucket to store Data
- Lambda function to enable the creation of custom S3 Resource
- Subnets for Redshift Serverless enabling High Availablility
- Redshift Serverless Workgroup
- Redshift Serverless Namespace

### Stack Output
- Redshift Serverless Workgroup Name
- Redshift Serverless Namespace Name
- Redshift Serverless Endpoint
Check the CloudFormation templates in the workshops under the reference section

## How to Run It
The CloudFormation template set up the s3 bucket, Redshift cluster and IAM roles. The EMR and Glue job will be created by airflow, which uses a boto3 (SDK) wrapper to create those resources.
1. (Optionally) Set Up Infrastructure using CloudFormation template
2. Install Airflow and Docker Compose on the device I used Cloud9 IDE (4 GB RAM 14 GB Disk storage, t3a.medium)
3. Write your pipeline in the Dag folder where Airflow was installed
4. Airflow should be running by default after installation with docker compose, view your project in a browser using http://localhost:8080 . For cloud9, use the preview button to view running applications. Select your dag and click the Run button to test your pipeline in the airflow UI.
5. You can create I am roles for access to different AWS resources, and attach them to the Ec2 instance used by cloud9, you can use the least privileged access for the specific bucket, but for development purposes, you can use AmazonS3FullAccess, AmazonElasticMapReduceFullAccess, AmazonRedshiftFullAccess for agility. If you use EMR serverless check this [page]([User access policy examples for EMR Serverless - Amazon EMR](https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/security-iam-user-access-policies.html)) to create policy in order access it

## Clean Up
If the resources were provisioned, manually delete s3 buckets, EMR application and Glue Database. You can delete CloudFormation stack if you used CloudFormation from the CloudFormation page.

## Contributing
To contribute 
fork the repo
Make a new branch
Add a new feature or make improvement to an existing feature
Commit your changes
Push your changes to the forked repo
Create a pull request

## References

- MWAA workshop https://catalog.workshops.aws/amazon-mwaa-for-analytics/en-US/workshop/m1-processing
- Redshift Immersion Day workshop [Redshift Immersion Day (workshops.aws)](https://catalog.us-east-1.prod.workshops.aws/workshops/9f29cdba-66c0-445e-8cbb-28a092cb5ba7/en-US/lab1) 
- Astronomer redshift setup 
- Blog on EMR on Stepfunctions [Orchestrate Amazon EMR Serverless jobs with AWS Step functions | AWS Big Data Blog](https://aws.amazon.com/blogs/big-data/orchestrate-amazon-emr-serverless-jobs-with-aws-step-functions/)
- c4j Youtube video [(15) Airflow Tutorial for Beginners - Full Course in 2 Hours 2022 - YouTube](https://www.youtube.com/watch?v=K9AnJ9_ZAXE)
- Airflow Installation, samples and use cases  
- [Running Airflow in Docker — Airflow Documentation (apache.org)](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
- [Amazon EMR Serverless Operators — apache-airflow-providers-amazon Documentation](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/emr/emr_serverless.html) 
- [Dish | Apache Airflow](https://airflow.apache.org/use-cases/dish/)

## License
This library is licensed under the MIT-0 License. See the LICENSE file.
