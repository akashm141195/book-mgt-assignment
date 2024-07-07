# book-mgt-assignment

The deployment steps is recorded in this document "Document_on_how_to_build_and_deploy.docx" found in the repository.

Points to remember:
- The deployment is not the best approach for deploying application, as we do ssh into a ec2 from github pipeline to run docker image.
- We can use terraform to automate the creation and deployment of the Application
- Also other deployment approaches can be using 
    * API gateway backed with Lambda, 
    * Running the container in ECS Cluster.
    * Running the API as Kubernetes Pods in a cluster.
  These approaches make sure high availability, highly secure and scalable. 
