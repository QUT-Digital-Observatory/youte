import sqlite3
import logging

logger = logging.getLogger(__name__)


def initialise_database(path, video_schema=True, channel_schema=True):
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS search_api_response(
            /*
            This table records the requests made to 
                Youtube API Search endpoint.
            Each row represents a URL of the request made.

            If a request has not been made, 
                it won't be in this database.
            */
            next_page_token PRIMARY KEY,
            request_url,
            status_code,
            response,
            total_results,
            retrieval_time
            );
                
                
        CREATE TABLE IF NOT EXISTS meta_data(
            /*
            This records all the meta data about the collection.
            
            As one database should contain only 
                one collection of a specific date range,
                this table should only have one row.
            */
            id PRIMARY KEY CHECK (id = 0),
            query,
            publishedAfter,
            publishedBefore
        );
        """
    )

    if video_schema:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS video_api_response(
                /*
                This table records the requests made to 
                    Youtube API Video endpoint.
                Each row represents a URL of the request made.

                If a request has not been made, 
                    it won't be in this database.
                */
                video_id PRIMARY KEY,
                response,
                retrieval_time
                );
                
                
            CREATE TABLE IF NOT EXISTS videos(
                 /*
                This table stores the processed data 
                    from Youtube API responses.
                */
                 video_id PRIMARY KEY,
                 published_at,
                 channel_id,
                 title,
                 description,
                 channel_title,
                 topic_categories,
                 upload_status,
                 view_count,
                 like_count,
                 comment_count
             );
            """
        )

    if channel_schema:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS channel_api_response(
                /*
                This table records the requests made to 
                    Youtube API Channel endpoint.
                Each row represents a URL of the request made.

                If a request has not been made, 
                    it won't be in this database.
                */
                channel_id primary key,
                response,
                retrieval_time
                );
                
            CREATE TABLE IF NOT EXISTS channels(
                 /*
                This table stores the processed data 
                    from Youtube API responses
                */
                 channel_id PRIMARY KEY,
                 ch_published_at,
                 ch_title,
                 ch_description,
                 ch_topic_categories,
                 ch_view_count,
                 ch_subscriber_count,
                 ch_video_count
             );
            """
        )

    conn.close()
    logger.debug(f'Tables created in {path}.')


def validate_metadata(path, input_query, input_start=None, input_end=None):
    with sqlite3.connect(path) as db:
        existing_data = [(row[0], row[1], row[3])
                         for row in
                         db.execute("""
                         select query, publishedAfter, publishedBefore 
                         from meta_data
                         """)
                         ]

        if existing_data:
            search_query, start, end = existing_data[0]
            if (start != input_start or
                    end != input_end or
                    search_query != input_query):
                raise Exception(
                    """
                    A database can only contain one collection of 
                        the same metadata.
                    Meta data already exist and do not match input. 
                        Check metadata.
                    """)

        elif not existing_data:
            db.execute(
                """
                insert into meta_data(id, query, 
                    publishedAfter, publishedBefore) 
                values (?,?,?,?)
                """,
                (0, input_query, input_start, input_end))

            logger.debug("Added meta data to metadata schema.")

