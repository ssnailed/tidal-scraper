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
    id: int
    name: str
    type: str
    picture: str


@dataclass
class Album:
    id: int
    title: str
    duration: int
    numberOfTracks: int
    numberOfVolumes: int
    releaseDate: str
    type: str
    version: str
    cover: str
    explicit: bool
    audioQuality: str
    audioModes: str
    artist: Artist
    artists: list


@dataclass
class Track:
    id: int
    title: str
    duration: int
    number: int
    volumeNumber: int
    version: str
    isrc: str
    explicit: bool
    audioQuality: str
    copyRight: str
    artist: Artist
    artists: Artist
    album: Album
    allowStreaming: bool


@dataclass
class StreamInfo:
    trackId: int
    audioQuality: str
    codecs: str
    encryptionKey: str
    url: str
