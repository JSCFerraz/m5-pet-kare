from django.forms import model_to_dict
from rest_framework.views import APIView, Request, Response, status
from pets.models import Pet
from traits.models import Trait
from groups.models import Group
from .serializers import PetSerializer
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404


class PetsView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        trait_query_param = request.query_params.get("trait", None)
        pets = Pet.objects.all()

        if trait_query_param != None:
            all_traits = Trait.objects.filter(name=trait_query_param).first()
            if all_traits:
                pets = all_traits.pets.all()
            else:
                pets = Pet.objects.none()

        result_page = self.paginate_queryset(pets, request)

        serializer = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = PetSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        trait_data = serializer.validated_data.pop("traits")
        group_data = serializer.validated_data.pop("group")

        group_obj = Group.objects.filter(
            scientific_name__iexact=group_data["scientific_name"]
        ).first()
        if not group_obj:
            group_obj = Group.objects.create(**group_data)

        pet_obj = Pet.objects.create(**serializer.validated_data, group=group_obj)

        for trait_dict in trait_data:
            trait_obj = Trait.objects.filter(name__iexact=trait_dict["name"]).first()

            if not trait_obj:
                trait_obj = Trait.objects.create(**trait_dict)

            pet_obj.traits.add(trait_obj)

        serializer = PetSerializer(instance=pet_obj)

        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class PetsDetailView(APIView):
    def get(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        serializer = PetSerializer(pet)

        return Response(serializer.data, status.HTTP_200_OK)

    def patch(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        serializer = PetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        for key, value in serializer.validated_data.items():
            if key == "traits":
                pet.traits.clear()
                for trait_dict in value:
                    trait_obj = Trait.objects.filter(
                        name__iexact=trait_dict["name"]
                    ).first()

                    if not trait_obj:
                        trait_obj = Trait.objects.create(**trait_dict)
                    pet.traits.add(trait_obj)

            elif key == "group":
                group_obj = Group.objects.filter(
                    scientific_name__iexact=value["scientific_name"]
                ).first()
                if not group_obj:
                    group_obj = Group.objects.create(**value)
                pet.group = group_obj
            else:
                setattr(pet, key, value)

        pet.save()
        serializer = PetSerializer(pet)

        return Response(serializer.data, status.HTTP_200_OK)

    def delete(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        pet.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
