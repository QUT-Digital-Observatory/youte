video_sql_table = {
    "create": """
        CREATE TABLE IF NOT EXISTS videos (
            video_id PRIMARY KEY,
            published_at,
            channel_id,
            title,
            description,
            thumbnails,   -- dictionary of thumbnail versions
            channel_title,
            tags,
            category_id,
            live_broadcast_content,
            default_language,
            localized_title,
            localized_description,
            default_audio_language,
            duration,
            dimension,
            definition,  -- high or standard definition video
            caption,
            licensed_content,
            region_allowed,
            region_blocked,
            yt_rating,  -- age-restricted content
            upload_status,
            rejection_reason,
            privacy_status,
            license,
            public_stats_viewable,
            made_for_kids,
            view_count,
            like_count,
            comment_count,
            topic_categories,
            recording_location
        )
              """,
    "insert": """
        INSERT OR REPLACE INTO videos
        VALUES (
            :video_id,
            :published_at,
            :channel_id,
            :title,
            :description,
            :thumbnails,
            :channel_title,
            :tags,
            :category_id,
            :live_broadcast_content,
            :default_language,
            :localized_title,
            :localized_description,
            :default_audio_language,
            :duration,
            :dimension,
            :definition,
            :caption,
            :licensed_content,
            :region_allowed,
            :region_blocked,
            :yt_rating,
            :upload_status,
            :rejection_reason,
            :privacy_status,
            :license,
            :public_stats_viewable,
            :made_for_kids,
            :view_count,
            :like_count,
            :comment_count,
            :topic_categories,
            :recording_location
        )
              """,
}

channel_sql_table = {
    "create": """
        CREATE TABLE IF NOT EXISTS channels(
            channel_id PRIMARY KEY,
            title,
            description,
            custom_url,
            published_at,
            thumbnails, -- dictionary of thumbnail versions
            default_language,
            localized_title,
            localized_description,
            country,
            related_playlists_likes, -- ID of the playlist containing
                                     -- the channel's liked videos
            related_playlists_uploads, -- playlist of channel's uploaded videos
            view_count,
            subscriber_count,
            hidden_subscriber_count,
            video_count,
            topic_ids, -- list of topic ids
            topic_categories, -- list of topic categories
            privacy_status,
            is_linked, -- channel data identifies user already linked with YT
            made_for_kids,
            keywords,
            moderate_comments,
            unsubscribed_trailer,
            content_owner,
            time_linked
            )
              """,
    "insert": """
        INSERT OR REPLACE INTO channels
        VALUES (
            :channel_id,
            :title,
            :description,
            :custom_url,
            :published_at,
            :thumbnails,
            :default_language,
            :localized_title,
            :localized_description,
            :country,
            :related_playlists_likes,
            :related_playlists_uploads,
            :view_count,
            :subscriber_count,
            :hidden_subscriber_count,
            :video_count,
            :topic_ids,
            :topic_categories,
            :privacy_status,
            :is_linked,
            :made_for_kids,
            :keywords,
            :moderate_comments,
            :unsubscribed_trailer,
            :content_owner,
            :time_linked
            )
              """,
}

comment_sql_table = {
    "create": """
        CREATE TABLE IF NOT EXISTS comments(
            comment_id PRIMARY KEY,
            video_id,
            channel_id,
            parent_id,
            can_reply,
            reply_count,
            text_display,
            text_original,
            author_name,
            author_channel_url,
            author_channel_id,
            can_rate,
            viewer_rating,
            like_count,
            published_at,
            updated_at
            )
             """,
    "insert": """
        INSERT OR REPLACE INTO comments
        VALUES (
            :comment_id,
            :video_id,
            :channel_id,
            :parent_id,
            :can_reply,
            :reply_count,
            :text_display,
            :text_original,
            :author_name,
            :author_channel_url,
            :author_channel_id,
            :can_rate,
            :viewer_rating,
            :like_count,
            :published_at,
            :updated_at
            )
            """,
}
