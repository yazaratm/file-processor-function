import logging
import azure.functions as func
import os
from azure.data.tables import TableServiceClient
from datetime import datetime

# Configuration - uses same storage account
STORAGE_CONNECTION_STRING = os.environ["AzureWebJobsStorage"]  # Uses function's built-in storage connection

def main(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob \n"
                f"Name: {myblob.name}\n"
                f"Blob Size: {myblob.length} bytes")

    # Extract file ID from blob name (format: "uploads/{file_id}_filename.txt")
    blob_name = myblob.name
    filename_parts = blob_name.split('/')[-1].split('_')
    file_id = filename_parts[0]  # First part is the UUID

    try:
        # Initialize Table client
        table_service = TableServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        table_client = table_service.get_table_client(table_name="filemetadata")

        # 1. Get current entity
        entity = table_client.get_entity(partition_key="files", row_key=file_id)
        
        # 2. Update status to "Processing"
        entity['status'] = 'Processing'
        table_client.update_entity(entity=entity)
        
        logging.info(f"Started processing file: {filename_parts[1]}")

        # 3. Simulate file processing
        # Example: If it's an image, create thumbnail
        if any(ext in blob_name.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
            # Simulate image processing
            logging.info(f"Simulating image processing for {blob_name}")
            # Add your actual image processing logic here
            
        # Simulate processing time
        import time
        time.sleep(5)  # Simulate 5 seconds of work

        # 4. Update status to "Completed"
        entity['status'] = 'Completed'
        entity['processed_time'] = datetime.utcnow().isoformat()
        entity['file_size_processed'] = myblob.length
        table_client.update_entity(entity=entity)

        logging.info(f"Successfully processed {blob_name}")

    except Exception as e:
        logging.error(f"Error processing blob {blob_name}: {str(e)}")
        
        # Update status to "Error"
        try:
            table_service = TableServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
            table_client = table_service.get_table_client(table_name="filemetadata")
            entity = table_client.get_entity(partition_key="files", row_key=file_id)
            entity['status'] = 'Error'
            entity['error_message'] = str(e)
            table_client.update_entity(entity=entity)
        except Exception as inner_e:
            logging.error(f"Could not update status to Error: {inner_e}")

