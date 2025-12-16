erDiagram

    MediaTypes {
        int media_type_id PK
        string type_name
    }

    MediaItems {
        int media_item_id PK
        string condition
        float purchase_price
        int media_type_id FK
        int release_id FK
    }

    VinylAttributes {
        int vinyl_id PK
        int media_item_id FK
        string size
        int sides_count
        int rpm
    }

    Releases {
        int release_id PK
        string title
        int release_year
        string label
        string country
    }

    Artists {
        int artist_id PK
        string name
        string artist_type
    }

    Tracks {
        int track_id PK
        int track_number
        string title
        int duration
        int release_id FK
    }

    Genres {
        int genre_id PK
        string genre_name
    }

    ReleaseArtists {
        int release_id FK
        int artist_id FK
    }

    TrackArtists {
        int track_id FK
        int artist_id FK
    }

    ReleaseGenres {
        int release_id FK
        int genre_id FK
    }

    %% Связи
    MediaTypes ||--o{ MediaItems : "1:M"
    Releases  ||--o{ MediaItems : "1:M"
    MediaItems ||--|| VinylAttributes : "1:1 (опц.)"

    Releases ||--o{ Tracks : "1:M"

    Artists ||--o{ ReleaseArtists : "M:M"
    Releases ||--o{ ReleaseArtists : ""

    Artists ||--o{ TrackArtists : "M:M"
    Tracks  ||--o{ TrackArtists : ""

    Genres  ||--o{ ReleaseGenres : "M:M"
    Releases ||--o{ ReleaseGenres : ""
