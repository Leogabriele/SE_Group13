private static void mergeSort(int[] array) {
    int length = array.length;
    if (length <= 1) return; // base case

    int middle = length / 2;
    int[] leftArray = new int[middle];
    int[] rightArray = new int[length - middle];

    int i = 0; // left array index
    int j = 0; // right array index

    for (int k = 0; k < length; k++) {
        if (k < middle) {
        leftArray[i] = array[k];
        i++;
        } else {
        rightArray[j] = array[k];
        j++;
        }
    }
    mergeSort(leftArray);
    mergeSort(rightArray);
    merge(leftArray, rightArray, array);
}

private static void merge(int[] leftArray, int[] rightArray, int[] array) {
    int leftSize = leftArray.length;
    int rightSize = rightArray.length;

    int i = 0; // original array index
    int l = 0; // left array index
    int r = 0; // right array index

    while (l < leftSize && r < rightSize) {
        if (leftArray[l] < rightArray[r]) {
        array[i] = leftArray[l];
        i++;
        l++;
        } else {
        array[i] = rightArray[r];
        i++;
        r++;
        }
    }
    while (l < leftSize) {
        array[i] = leftArray[l];
        i++;
        l++;
    }
    while (r < rightSize) {
        array[i] = rightArray[r];
        i++;
        r++;
    }
}