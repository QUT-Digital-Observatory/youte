video_sql_tables = {
    'create': """
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
    'insert': """
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
              """
}
