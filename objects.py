from dataclasses import dataclass


@dataclass
class Login:
    deviceCode: str
    userCode: str
    verificationUrl: str
    timeout: int
    interval: int


@dataclass
class Auth:
    userId: str
    countryCode: str
    accessToken: str
    refreshToken: str
    expiresIn: str


@dataclass
class Artist:
    id: int | None
    name: str | None
    type: str | None
    picture: str | None


@dataclass
class Album:
    id: int | None
    title: str | None
    duration: int | None
    numberOfTracks: int | None
    numberOfVideos: int | None
    numberOfVolumes: int | None
    releaseDate: str | None
    type: str | None
    version: str | None
    cover: str | None
    explicit: bool | None
    audioQuality: str | None
    audioModes: str | None
    artist: Artist | None
    artists: Artist | None


@dataclass
class Playlist:
    uuid: str | None
    title: str | None
    numberOfTracks: int | None
    numberOfVideos: int | None
    description: str | None
    duration: int | None
    image: str | None
    squareImage: str | None


@dataclass
class Track:
    id: int | None
    title: str | None
    duration: int | None
    trackNumber: int | None
    volumeNumber: int | None
    trackNumberOnPlaylist: int | None
    version: str | None
    isrc: str | None
    explicit: bool | None
    audioQuality: str | None
    copyRight: str | None
    artist: Artist | None
    artists: Artist | None
    album: Album | None
    allowStreaming: bool | None
    playlist: Playlist | None


@dataclass
class StreamResponse:
    trackid: int | None
    streamType: str | None
    assetPresentation: str | None
    audioMode: str | None
    audioQuality: str | None
    videoQuality: str | None
    manifestMimeType: str | None
    manifest: str | None
