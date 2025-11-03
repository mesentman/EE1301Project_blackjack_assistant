# Image Recgonition Webpage

## Datset used to train model

[Dataset](https://universe.roboflow.com/augmented-startups/playing-cards-ow27d/dataset/4#)

## How to install mkcert

Run these commands in Powershell

```pwsh
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

```pwsh
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

```pwsh
scoop bucket add extras
```

```pwsh
scoop install mkcert
```

```pwsh
mkcert -install
```

## How to have mobile device trust the SSL Certificate

Go to

```pwsh
mkcert -CAROOT
```

- Copy the `rootCA.pem`
- Download onto mobile device
- Install the profile and trust it <br>
  https://github.com/FiloSottile/mkcert?tab=readme-ov-file#mobile-devices